"""Check the published tasks with Harbor's own task loader."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from harbor.models.task.task import Task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=Path("tasks"))
    parser.add_argument("--source", type=Path, help="Optional original effective-cases.json")
    args = parser.parse_args()
    source = {}
    if args.source:
        source = {c["pair_id"]: c for c in json.loads(args.source.read_text())
                  if c["condition"] == "switched"}
    counts = Counter()
    step_count = 0
    for path in sorted(args.tasks.glob("*/*")):
        if not path.is_dir():
            continue
        task = Task(path)
        assert task.has_steps
        assert task.config.multi_step_reward_strategy.value == "final"
        assert task.config.metadata["split"] == path.parent.name
        assert task.config.steps[-1].name == "final"
        assert task.config.steps[-1].verifier.environment_mode.value == "separate"
        assert len(list(path.glob("steps/*/tests/contract.json"))) == 1
        environment = json.loads((path / "environment/environment.json").read_text())
        assert len(environment["workspaces"]) == 5
        assert task.config.steps[-1].artifacts[0].source == "/work/" + environment["focus_workspace"]
        for layer in environment["layers"]:
            assert (path / "environment" / layer["requirements"]).is_file()
            assert layer["source"].endswith(".tar.gz")
            assert (path / "environment" / layer["source"]).is_file()
        for workspace in environment["workspaces"]:
            assert workspace["url"].startswith("https://github.com/")
            for entry in workspace["overlays"]:
                if entry["mode"] != "delete":
                    blob = path / "environment/overlay-blobs" / entry["sha256"]
                    assert hashlib.sha256(blob.read_bytes()).hexdigest() == entry["sha256"]
        if source:
            turns = source[path.name]["turns"]
            assert len(turns) == len(task.config.steps)
            for turn, step in zip(turns, task.config.steps):
                assert (path / "steps" / step.name / "instruction.md").read_bytes() == turn["prompt"].encode("utf-8"), (path.name, step.name)
        counts[path.parent.name] += 1
        step_count += len(task.config.steps)
    assert counts == {"near": 100, "far": 100}, counts
    print(json.dumps({"tasks": sum(counts.values()), "splits": dict(counts),
                      "steps": step_count, "harbor_task_loading": "passed"}, indent=2))


if __name__ == "__main__":
    main()
