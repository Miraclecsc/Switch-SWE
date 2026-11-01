"""Export only final-step tests for upstream Harbor's separate verifier.

The caller owns task.toml and the environment. Merge returned ``artifacts`` and
``verifier`` into the final step; bake an independent, clean original focus
checkout (including .git) into /opt/focus-base BEFORE applying initial overlays.
The verifier image must provide the mapped Python, project dependencies, and
any required compiled extensions. No agent subclass or custom runner is used.

Source API: harbor-framework/harbor, ac533ec72bc506c8a6bf6f296ba6ab80707fad89,
docs-mintlify/tasks/separate-verifier.mdx. Artifacts return to their source paths.
Only runtime functions are emitted into the stdlib-only generated grader.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET


TEST_PATH = re.compile(
    r"(^|/)(_?tests?|testing)/|(^|/)test_[^/]+\.py$|_test\.py$|(^|/)conftest\.py$"
)
DIFF_HEADER = re.compile(r"^diff --git a/(.*?) b/(.*?)$", re.M)


def validate_targets(meta):
    groups = []
    for key in ("derived_fail_to_pass", "derived_pass_to_pass"):
        nodes = meta.get(key)
        if (not isinstance(nodes, list)
                or any(not isinstance(n, str) or not n for n in nodes)
                or len(nodes) != len(set(nodes))):
            raise ValueError(f"{key} must contain unique nonempty test IDs")
        groups.append(set(nodes))
    if not groups[0] or groups[0] & groups[1]:
        raise ValueError("F2P must be nonempty and disjoint from P2P")
    if meta.get("n_pass_to_pass", len(groups[1])) != len(groups[1]):
        raise ValueError("n_pass_to_pass differs from the P2P list")


def export_verifier(case, source_root, task_dir):
    """Return final-step TOML fields and environment requirements.

    source_root is the frozen release containing cohort.json. The bound pair
    source_release provides scoring and recipes; only case.task_id is exported.
    reference_patch is returned for the caller's oracle/qualification use, never
    written to the generated tests or contract.
    """
    if case["condition"] != "switched":
        raise ValueError("Only switched tasks may be exported")
    root = Path(source_root)
    rows = json.loads((root / "cohort.json").read_text())["pairs"]
    matches = [r for r in rows if r["pair_id"] == case["pair_id"]]
    if len(matches) != 1 or case["case_id"] not in matches[0]["case_ids"]:
        raise ValueError("Case is not uniquely bound in the frozen cohort")
    row = matches[0]
    pair_root = Path(row["source_release"])
    if not pair_root.is_absolute():
        pair_root = root / pair_root

    def bound(name):
        data = (pair_root / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != row["bindings"][name]:
            raise ValueError(f"Source hash mismatch: {name}")
        return json.loads(data)

    meta = bound("private/scoring.json")[case["task_id"]]
    recipe = bound("config/recipes.json")["cases"][case["pair_id"]]
    validate_targets(meta)
    focus = next(w for w in case["workspaces"]
                 if w["workspace"] == case["focus_workspace"])
    if (focus["repo"], focus["commit"]) != (meta["repo"], meta["base_commit"]):
        raise ValueError("Focus repo/commit differs from scoring contract")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", focus["workspace"]):
        raise ValueError("Invalid focus workspace")
    if recipe["runner"] not in {"pytest", "django"}:
        raise ValueError("Unsupported test runner")
    if set(recipe) - {"runner", "python", "env"}:
        raise ValueError("Unsupported recipe fields; do not silently drop build requirements")
    if not isinstance(recipe.get("python"), str) or not recipe["python"].startswith("/"):
        raise ValueError("Recipe must specify its absolute Python executable")
    if not isinstance(recipe.get("env"), dict) or any(
            not isinstance(k, str) or not isinstance(v, str)
            for k, v in recipe["env"].items()):
        raise ValueError("Recipe env must map strings to strings")
    patch = meta["test_patch"]
    heads = DIFF_HEADER.findall(patch)
    if not heads or len(heads) != len(re.findall(r"^diff --git ", patch, re.M)):
        raise ValueError("Unsupported hidden test patch headers")
    files = list(dict.fromkeys(b for _, b in heads
                              if TEST_PATH.search(b) and b.endswith(".py")
                              and not b.endswith("conftest.py")))
    if not files or any(p.startswith("/") or ".." in Path(p).parts for p in files):
        raise ValueError("Hidden patch has no safe Python test files")
    contract = {
        "case_id": case["case_id"], "task_id": case["task_id"],
        "repo": meta["repo"], "base_commit": meta["base_commit"],
        "derived_fail_to_pass": meta["derived_fail_to_pass"],
        "derived_pass_to_pass": meta["derived_pass_to_pass"],
        "recipe": dict(recipe), "test_files": files, "source_python": recipe["python"],
        "protected_paths": sorted({p for pair in heads for p in pair}),
        "base_path": "/opt/focus-base", "focus_path": "/work/" + focus["workspace"],
        "timeout_sec": 2400,
        "source_hashes": {k: row["bindings"][k]
                          for k in ("private/scoring.json", "config/recipes.json")},
    }
    # Public environment exporter replaces the frozen host-specific runtime.
    if recipe["python"].startswith("/opt/runtime/"):
        contract["recipe"]["python"] = "/opt/ssb/bin/python"
    contract["recipe"]["env"] = dict(recipe["env"], SSB_WORKSPACE=focus["workspace"])
    if meta["repo"] == "pandas-dev/pandas":
        contract["native_rebuild"] = ["/opt/ssb/rebuild-native.py"]
    tests = Path(task_dir) / "steps/final/tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    (tests / "test.patch").write_text(patch)
    runtime = (
        '"""Grade the final focus artifact in a fresh Harbor verifier."""\n'
        "from __future__ import annotations\n"
        "import argparse, json, os, re, shutil, signal, subprocess, tempfile\n"
        "from pathlib import Path\n"
        "import xml.etree.ElementTree as ET\n\n"
        f"TEST_PATH = re.compile({TEST_PATH.pattern!r})\n\n"
    )
    runtime += "\n\n".join(inspect.getsource(fn) for fn in (
        validate_targets, run, checked, git_env, collect_patch, junit,
        django_outcomes, run_tests, grade, main,
    ))
    runtime += '\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
    (tests / "grader.py").write_text(runtime)
    script = tests / "test.sh"
    script.write_text(
        "#!/bin/bash\nset -euo pipefail\n"
        "mkdir -p /logs/verifier\n"
        "rm -f /logs/verifier/reward.txt /logs/verifier/reward.json\n"
        "exec /usr/bin/python3 /tests/grader.py\n"
    )
    script.chmod(0o755)
    return {
        "artifacts": [{
            "source": contract["focus_path"], "destination": "focus",
            "exclude": [".git", ".venv", "venv", "__pycache__", "*.pyc",
                        ".pytest_cache", ".mypy_cache", ".ruff_cache"],
        }],
        "verifier": {"environment_mode": "separate", "timeout_sec": 10000},
        "base_path": contract["base_path"], "base_commit": meta["base_commit"],
        "python": contract["recipe"]["python"], "runner": recipe["runner"],
        "native_rebuild": contract.get("native_rebuild"),
        "reference_patch": meta["code_patch"],
        "n_f2p": len(meta["derived_fail_to_pass"]),
        "n_p2p": len(meta["derived_pass_to_pass"]),
        "tests_dir": str(tests),
        "submission": "final_focus_working_tree_including_committed_changes",
    }


def run(argv, cwd, *, env=None, timeout=120):
    """Bound subprocess trees so timed-out pytest children cannot leak."""
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True)
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, _ = p.communicate()
        return 124, out
    return p.returncode, out


def checked(argv, cwd, *, env=None):
    rc, output = run(argv, cwd, env=env)
    if rc:
        raise RuntimeError(f"{argv[0]} failed ({rc}): "
                           + output.decode(errors="replace")[-1000:])
    return output


def git_env():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
               GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env


def collect_patch(base, focus, control, contract):
    """Use only clean verifier Git metadata, even if the agent rewrote HEAD."""
    env = git_env()
    head = checked(["git", "rev-parse", "HEAD"], base, env=env).decode().strip()
    if head != contract["base_commit"]:
        raise RuntimeError("Verifier base is not at the original base_commit")
    if checked(["git", "status", "--porcelain", "--untracked-files=no"], base, env=env).strip():
        raise RuntimeError("Verifier base has tracked modifications")
    if not focus.is_dir():
        raise RuntimeError("Missing final focus artifact")
    checked(["git", "clone", "--shared", "--no-checkout", str(base), str(control)],
            base, env=env)
    cmd = ["git", "--git-dir=" + str(control / ".git"),
           "--work-tree=" + str(focus), "-c", "core.hooksPath=/dev/null",
           "-c", "core.fsmonitor=false"]
    checked(cmd + ["read-tree", head], control, env=env)
    checked(cmd + ["add", "-A", "--", "."], focus, env=env)
    raw = checked(cmd + ["diff", "--cached", "--no-renames", "--name-only",
                         "-z", head], control, env=env)
    paths = [os.fsdecode(p) for p in raw.split(b"\0") if p]
    paths = [p for p in paths if not TEST_PATH.search(p)
             and p not in contract["protected_paths"]]
    if not paths:
        return b""
    return checked(cmd + ["--literal-pathspecs", "diff", "--cached",
                          "--binary", "--full-index", "--no-ext-diff",
                          "--no-textconv", "--no-renames", head, "--", *paths],
                   control, env=env)


def junit(path):
    out = {}
    try:
        root = ET.parse(path)
    except (OSError, ET.ParseError):
        return out
    for tc in root.iter("testcase"):
        key = f"{tc.get('classname', '')}::{tc.get('name', '')}"
        tags = {x.tag for x in tc}
        state = ("error" if "error" in tags else "fail" if "failure" in tags
                 else "skip" if "skipped" in tags else "pass")
        if out.get(key, "pass") == "pass":
            out[key] = state
    return out


def django_outcomes(log):
    pattern = (r"(\w+) \(([\w.]+?)\)(?: \[[^\]]*\])? \.\.\. "
               r"(ok|FAIL|ERROR|skipped|expected failure|unexpected success)")
    statuses = {"ok": "pass", "FAIL": "fail", "ERROR": "error", "skipped": "skip",
                "expected failure": "skip", "unexpected success": "fail"}
    out = {}
    for _, node, state in re.findall(pattern, log):
        if out.get(node, "pass") == "pass":
            out[node] = statuses[state]
    return out


def run_tests(contract, repo, out, tag):
    recipe = contract["recipe"]
    env = dict(os.environ, **recipe["env"])
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if contract.get("native_rebuild"):
        rc, raw = run([*contract["native_rebuild"], str(repo)], repo, env=env,
                      timeout=contract["timeout_sec"])
        (out / (tag + ".build.log")).write_bytes(raw)
        if rc:
            return rc, {}
    # Resolve imports against the patched source, not an installed reference.
    source_paths = [str(repo), str(repo / "src")]
    xml = out / (tag + ".xml")
    xml.unlink(missing_ok=True)
    if recipe["runner"] == "django":
        modules = [re.sub(r"^tests/", "", p)[:-3].replace("/", ".")
                   for p in contract["test_files"]]
        cmd = [recipe["python"], "tests/runtests.py", *modules,
               "--verbosity", "2", "--parallel", "1"]
        source_paths.insert(0, str(repo / "tests"))
    else:
        cmd = [recipe["python"], "-m", "pytest", *contract["test_files"],
               "-p", "no:cacheprovider", "-p", "no:randomly", "--no-header",
               "-q", "-rN", "--junit-xml=" + str(xml), "-o", "junit_family=xunit2"]
    env["PYTHONPATH"] = os.pathsep.join(source_paths)
    rc, raw = run(cmd, repo, env=env, timeout=contract["timeout_sec"])
    log = raw.decode(errors="replace")
    (out / (tag + ".log")).write_text(log)
    outcomes = django_outcomes(log) if recipe["runner"] == "django" else junit(xml)
    (out / (tag + ".outcomes.json")).write_text(json.dumps(outcomes, indent=2) + "\n")
    return rc, outcomes


def grade(tests, base, focus, out):
    """Grade a transferred artifact; infrastructure errors produce no reward."""
    tests, base, focus, out = (Path(p).resolve() for p in (tests, base, focus, out))
    out.mkdir(parents=True, exist_ok=True)
    for name in ("reward.txt", "reward.json"):
        (out / name).unlink(missing_ok=True)
    result = {"status": "error", "passed": False}
    try:
        contract = json.loads((tests / "contract.json").read_text())
        validate_targets(contract)
        required = contract["derived_fail_to_pass"] + contract["derived_pass_to_pass"]
        with tempfile.TemporaryDirectory(prefix="switch-swe-verifier-") as scratch:
            scratch = Path(scratch)
            patch = collect_patch(base, focus, scratch / "control", contract)
            candidate = out / "candidate.patch"
            candidate.write_bytes(patch)
            repo = scratch / "repo"
            checked(["git", "clone", "--shared", str(base), str(repo)], base, env=git_env())
            # Preserve trusted, prebuilt extensions and runtime fixtures, too.
            shutil.copytree(base, repo, dirs_exist_ok=True, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            checked(["git", "apply", "--whitespace=nowarn", str(tests / "test.patch")],
                    repo, env=git_env())
            if patch:
                rc, log = run(["git", "apply", "--whitespace=nowarn", str(candidate)],
                              repo, env=git_env())
                if rc:
                    raise RuntimeError("Collected code patch failed to apply: "
                                       + log.decode(errors="replace")[-500:])
            rc, outcomes = run_tests(contract, repo, out, "candidate")
            if rc not in (0, 1) or not all(k in outcomes for k in required):
                # Distinguish a broken submission from a broken image/contract.
                if patch:
                    checked(["git", "apply", "-R", str(candidate)], repo, env=git_env())
                control_rc, control_out = run_tests(contract, repo, out, "base_diagnostic")
                if control_rc not in (0, 1) or not all(k in control_out for k in required):
                    raise RuntimeError("Base environment cannot collect the required F2P/P2P tests")
            f2p = [k for k in contract["derived_fail_to_pass"] if outcomes.get(k) != "pass"]
            p2p = [k for k in contract["derived_pass_to_pass"] if outcomes.get(k) != "pass"]
            result = {
                "status": "graded", "passed": rc in (0, 1) and not f2p and not p2p,
                "n_f2p": len(contract["derived_fail_to_pass"]),
                "n_p2p": len(contract["derived_pass_to_pass"]),
                "tests_run": len(outcomes), "test_exit_code": rc,
                "f2p_not_passing": f2p, "p2p_not_passing": p2p,
            }
    except Exception as exc:
        result["reason"] = str(exc)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] == "graded":
        (out / "reward.txt").write_text("1\n" if result["passed"] else "0\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--focus", type=Path)
    parser.add_argument("--out", type=Path, default=Path("/logs/verifier"))
    args = parser.parse_args()
    contract = json.loads((args.tests / "contract.json").read_text())
    result = grade(args.tests, args.base or contract["base_path"],
                   args.focus or contract["focus_path"], args.out)
    print(json.dumps(result))
    return 0 if result["status"] == "graded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
