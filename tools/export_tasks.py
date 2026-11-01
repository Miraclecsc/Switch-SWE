"""Convert the frozen switched cohort into native Harbor multi-step tasks."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

from export_environments import export_environment
from export_verifier import export_verifier

SOURCE_SHA256 = "a47fefc8d3fc7251a25a56c74e5dd56637c7507cde1bcb085d921cf47d77da86"
HARBOR_COMMIT = "ac533ec72bc506c8a6bf6f296ba6ab80707fad89"


def write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def export_task(case, source, output):
    split = {3: "far", 4: "near"}[case["tier"]]
    task = output / split / case["pair_id"]
    task.mkdir(parents=True)
    for index, turn in enumerate(case["turns"]):
        name = "final" if index == len(case["turns"]) - 1 else f"turn-{index + 1:02d}"
        write(task / "steps" / name / "instruction.md", turn["prompt"])
    write(task / "solution/solve.sh", "#!/bin/bash\ntrue\n", True)
    # Harbor requires a test entry point for each step. Only the final step
    # contributes a task score; an incomplete session retains reward zero.
    write(task / "tests/test.sh",
          "#!/bin/bash\nmkdir -p /logs/verifier\nprintf '0\\n' > /logs/verifier/reward.txt\n",
          True)
    verification = export_verifier(case, source, task)
    environment = export_environment(case, source, task)
    if environment["blockers"]:
        raise ValueError(f'{case["pair_id"]}: {environment["blockers"]}')
    focus_repo = next(w["repo"] for w in case["workspaces"]
                      if w["workspace"] == case["focus_workspace"])
    config = [
        'schema_version = "1.4"',
        'multi_step_reward_strategy = "final"',
        "",
        "[metadata]",
        f'split = "{split}"',
        f'repository = "{focus_repo}"',
        f'source_id = "{case["pair_id"]}"',
        'category = "software-engineering"',
        'tags = ["switch-swe", "multi-step", "' + split + '"]',
        f'harbor_commit = "{HARBOR_COMMIT}"',
        "",
        "[agent]",
        "timeout_sec = 900",
        'user = "agent"',
        "",
        "[environment]",
        "build_timeout_sec = 3600",
        "cpus = 4",
        "memory_mb = 16384",
        "storage_mb = 30720",
        'workdir = "/work"',
        "",
        "[verifier]",
        "timeout_sec = 30",
        'environment_mode = "shared"',
    ]
    for index, _ in enumerate(case["turns"]):
        name = "final" if index == len(case["turns"]) - 1 else f"turn-{index + 1:02d}"
        config += ["", "[[steps]]", f'name = "{name}"']
        if name == "final":
            for artifact in verification["artifacts"]:
                config += ["", "[[steps.artifacts]]",
                           "source = " + json.dumps(artifact["source"]),
                           "destination = " + json.dumps(artifact["destination"])]
                if artifact.get("exclude"):
                    config.append("exclude = " + json.dumps(artifact["exclude"]))
            config += ["", "[steps.verifier]",
                       'environment_mode = "separate"',
                       f'timeout_sec = {verification["verifier"]["timeout_sec"]}']
    write(task / "task.toml", "\n".join(config) + "\n")
    write(task / "steps/final/solution/reference.patch", verification["reference_patch"])
    focus = "/work/" + case["focus_workspace"]
    write(task / "steps/final/solution/solve.sh",
          "#!/bin/bash\nset -e\n"
          f'git -C {focus} reset --hard {verification["base_commit"]}\n'
          f"git -C {focus} clean -fdx\n"
          f"git -C {focus} apply /solution/reference.patch\n", True)
    return {"task": case["pair_id"], "split": split, "steps": len(case["turns"]),
            "f2p": verification["n_f2p"], "p2p": verification["n_p2p"],
            "environment": environment}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Original fixed200-v1 directory with cohort and effective cases")
    parser.add_argument("--output", type=Path, default=Path("tasks"))
    parser.add_argument("--case", action="append", help="Export selected pair IDs")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--report", type=Path, help="Optional maintainer build report outside the tasks")
    args = parser.parse_args()
    raw = (args.source / "effective-cases.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Expected the frozen September 16 effective cases")
    cases = [c for c in json.loads(raw) if c["condition"] == "switched"]
    if len(cases) != 200 or Counter(c["tier"] for c in cases) != {3: 100, 4: 100}:
        raise ValueError("Expected 100 near and 100 far switched sessions")
    if args.case:
        cases = [c for c in cases if c["pair_id"] in args.case]
        if len(cases) != len(set(args.case)):
            raise ValueError("Unknown selected case")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda c: export_task(c, args.source, args.output), cases))
    report = {"tasks": len(results), "steps": sum(r["steps"] for r in results),
              "splits": dict(Counter(r["split"] for r in results)), "results": results}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
