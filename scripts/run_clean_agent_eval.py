#!/usr/bin/env python3
"""Run SessionSwitchBench cases in isolated controller/answer-agent workspaces.

The controller owns the benchmark JSON, clones repositories, strips `.git`, sends
one prompt at a time, and records the final focus patch. The answer agent only
sees the prepared workspace and the current prompt.
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any


@dataclass(frozen=True)
class RepoSpec:
    repo: str
    base_commit: str

    @property
    def safe_name(self) -> str:
        return f"{self.repo.replace('/', '__')}__{self.base_commit[:12]}"


def run(
    cmd: list[str] | str,
    *,
    cwd: Path | None = None,
    timeout: int,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    shell: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        shell=shell,
        check=False,
    )


def load_cases(data_dir: Path, split: str) -> list[dict[str, Any]]:
    filename = "focus_control_cases.json" if split == "control" else "session_cases.json"
    with (data_dir / filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def select_cases(
    cases: list[dict[str, Any]], case_ids: set[str] | None, max_cases: int | None
) -> list[dict[str, Any]]:
    if case_ids:
        cases = [c for c in cases if c.get("case_id") in case_ids]
    if max_cases is not None:
        cases = cases[:max_cases]
    return cases


def repo_url(repo: str, template: str) -> str:
    owner, name = repo.split("/", 1)
    return template.format(repo=repo, owner=owner, name=name)


def clone_checkout(
    spec: RepoSpec,
    *,
    dest: Path,
    url_template: str,
    timeout: int,
) -> None:
    url = repo_url(spec.repo, url_template)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["git", "clone", "--no-checkout", "--filter=blob:none", "--no-tags", url, str(dest)]
    cp = run(cmd, timeout=timeout)
    if cp.returncode != 0:
        raise RuntimeError(f"git clone failed for {spec.repo}: {cp.stderr[-2000:]}")

    fetch = run(
        ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", spec.base_commit],
        timeout=timeout,
    )
    if fetch.returncode != 0:
        fetch = run(["git", "-C", str(dest), "fetch", "origin", spec.base_commit], timeout=timeout)
    if fetch.returncode != 0:
        raise RuntimeError(f"git fetch failed for {spec.repo}@{spec.base_commit}: {fetch.stderr[-2000:]}")

    checkout = run(["git", "-C", str(dest), "checkout", "--detach", spec.base_commit], timeout=timeout)
    if checkout.returncode != 0:
        raise RuntimeError(f"git checkout failed for {spec.repo}@{spec.base_commit}: {checkout.stderr[-2000:]}")


def strip_paths(repo_dir: Path, strip_names: list[str]) -> None:
    for rel in strip_names:
        target = repo_dir / rel
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()


def copy_base_snapshot(src: Path, dst: Path, strip_names: list[str]) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    ignore = shutil.ignore_patterns(*strip_names, "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
    shutil.copytree(src, dst, ignore=ignore)


def repo_specs_for_case(case: dict[str, Any]) -> list[RepoSpec]:
    specs: dict[tuple[str, str], RepoSpec] = {}
    for turn in case.get("turns", []):
        repo = turn.get("repo")
        commit = turn.get("base_commit")
        if repo and commit:
            specs[(repo, commit)] = RepoSpec(repo, commit)
    return list(specs.values())


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass

    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    for candidate in reversed(fenced):
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            continue

    starts = [m.start() for m in re.finditer(r"\{", text)]
    for start in reversed(starts):
        depth = 0
        in_string = False
        escape = False
        for pos in range(start, len(text)):
            ch = text[pos]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start : pos + 1])
                        return obj if isinstance(obj, dict) else None
                    except json.JSONDecodeError:
                        break
    return None


def is_probably_text(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        return b"\0" not in chunk
    except OSError:
        return False


def collect_diff(base: Path, modified: Path) -> str:
    base_files = {
        p.relative_to(base)
        for p in base.rglob("*")
        if p.is_file() and ".git" not in p.parts and not any(part.startswith(".ssb") for part in p.parts)
    }
    mod_files = {
        p.relative_to(modified)
        for p in modified.rglob("*")
        if p.is_file() and ".git" not in p.parts and not any(part.startswith(".ssb") for part in p.parts)
    }
    hunks: list[str] = []
    for rel in sorted(base_files | mod_files):
        a = base / rel
        b = modified / rel
        if a.exists() and b.exists() and a.read_bytes() == b.read_bytes():
            continue
        if (a.exists() and not is_probably_text(a)) or (b.exists() and not is_probably_text(b)):
            continue
        old = a.read_text(errors="replace").splitlines(keepends=True) if a.exists() else []
        new = b.read_text(errors="replace").splitlines(keepends=True) if b.exists() else []
        hunks.append(f"diff --git a/{rel.as_posix()} b/{rel.as_posix()}\n")
        if not a.exists():
            hunks.append("new file mode 100644\n")
        if not b.exists():
            hunks.append("deleted file mode 100644\n")
        hunks.extend(
            difflib.unified_diff(
                old,
                new,
                fromfile=f"a/{rel.as_posix()}",
                tofile=f"b/{rel.as_posix()}",
            )
        )
    return "".join(hunks)


def render_command(template: str, env: dict[str, str]) -> str:
    return Template(template).safe_substitute(env)


def run_score_command(
    command: str,
    *,
    env: dict[str, str],
    cwd: Path,
    timeout: int,
) -> dict[str, Any]:
    cp = run(render_command(command, env), cwd=cwd, timeout=timeout, env=env, shell=True)
    parsed = extract_json_object(cp.stdout) or extract_json_object(cp.stderr)
    return {
        "returncode": cp.returncode,
        "stdout_tail": cp.stdout[-4000:],
        "stderr_tail": cp.stderr[-4000:],
        "parsed": parsed,
    }


def case_result_path(out_dir: Path, case_id: str) -> Path:
    return out_dir / "cases" / case_id / "result.json"


def run_case(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    case_id = case["case_id"]
    out_case = args.out_dir / "cases" / case_id
    result_file = case_result_path(args.out_dir, case_id)
    if args.resume and result_file.exists():
        return json.loads(result_file.read_text(encoding="utf-8"))

    answer_root = args.work_root / "answer_workspaces" / case_id
    controller_root = args.work_root / "controller_state" / case_id
    repos_root = answer_root / "repos"
    base_root = controller_root / "base_repos"
    out_case.mkdir(parents=True, exist_ok=True)
    controller_root.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "case_id": case_id,
        "focus_task_id": case.get("focus_task_id"),
        "split": args.split,
        "status": "started",
        "turns": [],
        "patch": "",
        "patch_source": None,
        "score": None,
    }

    try:
        specs = repo_specs_for_case(case)
        if args.dry_run:
            result.update(
                {
                    "status": "dry_run",
                    "repos": [{"repo": s.repo, "base_commit": s.base_commit} for s in specs],
                    "turn_count": len(case.get("turns", [])),
                }
            )
            return result

        if answer_root.exists():
            shutil.rmtree(answer_root)
        repos_root.mkdir(parents=True, exist_ok=True)

        repo_paths: dict[tuple[str, str], Path] = {}
        base_paths: dict[tuple[str, str], Path] = {}
        for spec in specs:
            repo_dir = repos_root / spec.safe_name
            clone_checkout(spec, dest=repo_dir, url_template=args.repo_url_template, timeout=args.git_timeout)
            base_dir = base_root / spec.safe_name
            copy_base_snapshot(repo_dir, base_dir, args.strip_path)
            strip_paths(repo_dir, args.strip_path)
            repo_paths[(spec.repo, spec.base_commit)] = repo_dir
            base_paths[(spec.repo, spec.base_commit)] = base_dir

        if args.prepare_only:
            result.update({"status": "prepared", "workspace": str(answer_root)})
            return result

        env_base = os.environ.copy()
        env_base.update(
            {
                "SSB_CASE_ID": case_id,
                "SSB_RELEASE_ROOT": str(Path(__file__).resolve().parents[1]),
                "SSB_CASE_WORKSPACE": str(answer_root),
                "SSB_AGENT_SESSION_DIR": str(answer_root / ".ssb_agent_session"),
                "SSB_REPOS_ROOT": str(repos_root),
                "SSB_FOCUS_TASK_ID": str(case.get("focus_task_id")),
            }
        )
        (answer_root / ".ssb_agent_session").mkdir(parents=True, exist_ok=True)

        final_stdout = ""
        final_stderr = ""
        for turn in case.get("turns", []):
            prompt_file = out_case / f"{turn['turn_index']:03d}_{turn['turn_label']}.prompt.txt"
            stdout_file = out_case / f"{turn['turn_index']:03d}_{turn['turn_label']}.stdout.txt"
            stderr_file = out_case / f"{turn['turn_index']:03d}_{turn['turn_label']}.stderr.txt"
            prompt_file.write_text(turn.get("prompt_text", ""), encoding="utf-8")

            turn_repo_path = repo_paths.get((turn.get("repo"), turn.get("base_commit")))
            env = env_base.copy()
            env.update(
                {
                    "SSB_PROMPT_FILE": str(prompt_file),
                    "SSB_TURN_INDEX": str(turn.get("turn_index")),
                    "SSB_TURN_LABEL": str(turn.get("turn_label")),
                    "SSB_TURN_ID": str(turn.get("turn_id")),
                    "SSB_TURN_TASK_ID": str(turn.get("task_id")),
                    "SSB_TURN_REPO": str(turn.get("repo")),
                    "SSB_TURN_REPO_PATH": str(turn_repo_path or ""),
                    "SSB_TURN_STAGE_ID": str(turn.get("stage_id")),
                    "SSB_TURN_ROLE": str(turn.get("role")),
                    "SSB_TURN_SCORED": str(bool(turn.get("scored"))).lower(),
                }
            )
            command = render_command(args.agent_command, env)
            started = time.time()
            cp = run(
                command,
                cwd=answer_root,
                timeout=args.turn_timeout,
                env=env,
                input_text=turn.get("prompt_text", ""),
                shell=True,
            )
            stdout_file.write_text(cp.stdout, encoding="utf-8")
            stderr_file.write_text(cp.stderr, encoding="utf-8")
            row = {
                "turn_label": turn.get("turn_label"),
                "turn_id": turn.get("turn_id"),
                "task_id": turn.get("task_id"),
                "role": turn.get("role"),
                "scored": turn.get("scored"),
                "returncode": cp.returncode,
                "seconds": round(time.time() - started, 3),
            }
            result["turns"].append(row)
            if cp.returncode != 0 and args.fail_fast_turn:
                raise RuntimeError(f"answer agent failed on {turn.get('turn_label')}: {cp.stderr[-1000:]}")
            if turn.get("scored"):
                final_stdout = cp.stdout
                final_stderr = cp.stderr

        final_obj = extract_json_object(final_stdout) or extract_json_object(final_stderr) or {}
        patch = final_obj.get("patch") if isinstance(final_obj.get("patch"), str) else ""
        patch_source = "answer_json" if patch else None

        focus_turn = next(t for t in case["turns"] if t.get("scored"))
        focus_key = (focus_turn.get("repo"), focus_turn.get("base_commit"))
        if not patch and focus_key in repo_paths:
            patch = collect_diff(base_paths[focus_key], repo_paths[focus_key])
            patch_source = "focus_repo_diff" if patch else "empty"

        patch_file = out_case / "final_focus_patch.diff"
        patch_file.write_text(patch, encoding="utf-8")
        result.update({"patch": patch, "patch_source": patch_source or "empty"})

        submission = {
            "case_id": case_id,
            "task_id": case.get("focus_task_id"),
            "patch": patch,
            "patch_source": result["patch_source"],
        }
        (out_case / "submission.json").write_text(
            json.dumps(submission, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if args.score_command:
            score_env = env_base.copy()
            score_env.update(
                {
                    "SSB_PATCH_FILE": str(patch_file),
                    "SSB_SUBMISSION_FILE": str(out_case / "submission.json"),
                    "SSB_RESULT_DIR": str(out_case),
                    "SSB_FOCUS_REPO": str(focus_turn.get("repo")),
                    "SSB_FOCUS_BASE_COMMIT": str(focus_turn.get("base_commit")),
                }
            )
            result["score"] = run_score_command(
                args.score_command,
                env=score_env,
                cwd=answer_root,
                timeout=args.score_timeout,
            )

        result["status"] = "completed"
        return result
    except subprocess.TimeoutExpired as exc:
        result.update({"status": "timeout", "error": str(exc)})
        return result
    except Exception as exc:  # noqa: BLE001 - controller must keep batch alive.
        result.update({"status": "error", "error": str(exc)})
        return result
    finally:
        out_case.mkdir(parents=True, exist_ok=True)
        result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.keep_workspaces and not args.prepare_only:
            shutil.rmtree(answer_root, ignore_errors=True)
            shutil.rmtree(controller_root, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--split", choices=["switched", "control"], default="switched")
    ap.add_argument("--case-id", action="append", default=[])
    ap.add_argument("--max-cases", type=int)
    ap.add_argument("--out-dir", type=Path, default=Path("runs/eval_out"))
    ap.add_argument("--work-root", type=Path, default=Path("runs/eval_work"))
    ap.add_argument("--repo-url-template", default="https://github.com/{repo}.git")
    ap.add_argument(
        "--agent-command",
        default="python3 $SSB_RELEASE_ROOT/examples/agent_adapters/echo_agent.py",
    )
    ap.add_argument("--score-command")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--turn-timeout", type=int, default=450)
    ap.add_argument("--score-timeout", type=int, default=900)
    ap.add_argument("--git-timeout", type=int, default=900)
    ap.add_argument("--strip-path", action="append", default=[".git"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--keep-workspaces", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--fail-fast-turn", action="store_true")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    cases = select_cases(load_cases(args.data_dir, args.split), set(args.case_id) or None, args.max_cases)
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    with futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = [pool.submit(run_case, case, args) for case in cases]
        for fut in futures.as_completed(futs):
            result = fut.result()
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ("case_id", "status", "patch_source")}, ensure_ascii=False))

    submissions_path = args.out_dir / "submissions.jsonl"
    summary_path = args.out_dir / "summary.json"
    with submissions_path.open("w", encoding="utf-8") as f:
        for result in results:
            f.write(
                json.dumps(
                    {
                        "case_id": result.get("case_id"),
                        "task_id": result.get("focus_task_id"),
                        "patch": result.get("patch", ""),
                        "patch_source": result.get("patch_source"),
                        "status": result.get("status"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    summary = {
        "attempted": len(results),
        "completed": sum(r.get("status") == "completed" for r in results),
        "dry_run": sum(r.get("status") == "dry_run" for r in results),
        "prepared": sum(r.get("status") == "prepared" for r in results),
        "timeout": sum(r.get("status") == "timeout" for r in results),
        "error": sum(r.get("status") == "error" for r in results),
        "submissions": str(submissions_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["error"] == 0 and summary["timeout"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
