#!/usr/bin/env python3
"""Verify SessionSwitchBench release invariants."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LEAK_PATTERNS = [
    re.compile(r"\btarget\s+areas?\b", re.I),
    re.compile(r"\btarget\s+files?\b", re.I),
    re.compile(r"\breference\s+patch\b", re.I),
    re.compile(r"\boracle\b", re.I),
    re.compile(r"\bhidden\s+tests?\b", re.I),
    re.compile(r"https://github\.com/.+/(pull|commit)/", re.I),
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_cases(cases: list[dict[str, Any]], *, expected: int, controls: bool) -> list[str]:
    errors: list[str] = []
    if len(cases) != expected:
        errors.append(f"case_count={len(cases)} expected={expected}")

    focus_ids = [case.get("focus_task_id") for case in cases]
    if len(set(focus_ids)) != len(focus_ids):
        errors.append("focus_task_id is not unique")

    for idx, case in enumerate(cases):
        cid = case.get("case_id", f"case[{idx}]")
        turns = case.get("turns") or []
        if not turns:
            errors.append(f"{cid}: no turns")
            continue

        scored = [t for t in turns if t.get("scored")]
        if len(scored) != 1:
            errors.append(f"{cid}: scored_turn_count={len(scored)}")
            continue

        final = scored[0]
        if final is not turns[-1]:
            errors.append(f"{cid}: scored final turn is not last")
        if final.get("role") != "focus":
            errors.append(f"{cid}: scored turn role is {final.get('role')}")
        if final.get("task_id") != case.get("focus_task_id"):
            errors.append(f"{cid}: scored task does not match focus task")
        if final.get("turn_label") != case.get("primary_scored_turn"):
            errors.append(f"{cid}: primary_scored_turn mismatch")

        labels = [t.get("turn_label") for t in turns]
        if labels != case.get("turn_sequence") and labels != case.get("turn_order"):
            errors.append(f"{cid}: turn labels do not match turn_sequence/turn_order")

        if not controls:
            focus_positions = [i for i, t in enumerate(turns) if t.get("role") == "focus"]
            if not focus_positions or focus_positions[0] > 2:
                errors.append(f"{cid}: first focus turn is not within first three turns")
            for t in turns[:-1]:
                if t.get("role") == "interruption" and t.get("scored"):
                    errors.append(f"{cid}: interruption turn is scored")

        for turn in turns:
            prompt = turn.get("prompt_text") or ""
            for pattern in LEAK_PATTERNS:
                if pattern.search(prompt):
                    errors.append(f"{cid}/{turn.get('turn_label')}: leakage pattern {pattern.pattern}")

    return errors


def verify_tasks(tasks: list[dict[str, Any]], *, expected: int) -> list[str]:
    errors: list[str] = []
    if len(tasks) != expected:
        errors.append(f"task_count={len(tasks)} expected={expected}")
    task_ids = [t.get("task_id") for t in tasks]
    if len(set(task_ids)) != len(task_ids):
        errors.append("task_id is not unique")
    for task in tasks:
        tid = task.get("task_id", "<missing>")
        stages = task.get("workflow_stages") or []
        if len(stages) < 2:
            errors.append(f"{tid}: fewer than two workflow stages")
        finals = [s for s in stages if s.get("expects_final_patch")]
        if len(finals) != 1:
            errors.append(f"{tid}: final_stage_count={len(finals)}")
        elif finals[0] is not stages[-1]:
            errors.append(f"{tid}: final stage is not last")
        if any("source_urls" in s for s in stages):
            errors.append(f"{tid}: stage contains source_urls")
        for forbidden in ("source_urls", "reference_patch", "test_patch", "implementation_files", "test_patch_files"):
            if forbidden in task:
                errors.append(f"{tid}: public task contains forbidden field {forbidden}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--expected-count", type=int, default=500)
    ap.add_argument("--write-report", action="store_true")
    args = ap.parse_args()

    tasks = load_json(args.data_dir / "tasks.json")
    cases = load_json(args.data_dir / "session_cases.json")
    controls = load_json(args.data_dir / "focus_control_cases.json")

    errors: list[str] = []
    errors.extend(verify_tasks(tasks, expected=args.expected_count))
    errors.extend(verify_cases(cases, expected=args.expected_count, controls=False))
    errors.extend(verify_cases(controls, expected=args.expected_count, controls=True))

    report = {
        "status": "pass" if not errors else "fail",
        "expected_count": args.expected_count,
        "tasks": len(tasks),
        "session_cases": len(cases),
        "focus_control_cases": len(controls),
        "unique_focus_tasks": len({c.get("focus_task_id") for c in cases}),
        "errors": errors,
    }
    if args.write_report:
        (args.data_dir / "release_verification.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
