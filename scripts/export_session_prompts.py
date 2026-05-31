from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_cases(path: str, max_cases: int) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TypeError("cases file must contain a list")
    return data[:max_cases] if max_cases else data


def safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in s)


def main() -> None:
    ap = argparse.ArgumentParser(description="Export SessionSwitchBench session prompts for external coding-agent runs")
    ap.add_argument("--cases", default="data/session_cases.json")
    ap.add_argument("--out-dir", default="runs/session_prompts")
    ap.add_argument("--max-cases", type=int, default=0)
    ap.add_argument("--submission-template", default="runs/submission_template.jsonl")
    args = ap.parse_args()

    cases = load_cases(args.cases, args.max_cases)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    template_rows = []
    index = []
    for case in cases:
        case_id = str(case["case_id"])
        case_dir = out_dir / safe_name(case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        for turn in case.get("turns", []):
            turn_idx = int(turn.get("turn_index", turn.get("turn", 0)))
            turn_label = str(turn.get("turn_id") or turn.get("slot") or f"turn_{turn_idx:02d}")
            prompt = str(turn.get("prompt_text", turn.get("prompt", "")))
            (case_dir / f"{turn_idx:02d}_{safe_name(turn_label)}.txt").write_text(prompt, encoding="utf-8")
        meta = {
            "case_id": case_id,
            "pair_id": case.get("pair_id", ""),
            "kind": case.get("case_kind", case.get("kind", "")),
            "focus_task_id": case.get("focus_task_id", ""),
            "focus_repo": case.get("focus_repo", ""),
            "matched_group_id": case.get("matched_group_id", ""),
            "scored_task_ids": case.get("scored_task_ids", []),
            "primary_scored_turn": case.get("primary_scored_turn", ""),
            "scored_turn_ids": case.get("scored_turn_ids", []),
            "turns": len(case.get("turns", [])),
            "protocol_version": case.get("protocol_version", ""),
            "session_policy": case.get("session_policy", {}),
            "score_policy": case.get("score_policy", {}),
        }
        (case_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append(meta | {"prompt_dir": str(case_dir)})
        template_rows.append(
            {
                "case_id": case_id,
                "task_id": case.get("focus_task_id", ""),
                "matched_group_id": case.get("matched_group_id", ""),
                "primary_scored_turn": case.get("primary_scored_turn", ""),
                "model": "",
                "agent_scaffold": "",
                "patch": "diff --git a/...",
            }
        )

    (out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.submission_template).parent.mkdir(parents=True, exist_ok=True)
    Path(args.submission_template).write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in template_rows) + ("\n" if template_rows else ""),
        encoding="utf-8",
    )
    print(f"Wrote {out_dir}")
    print(f"Wrote {args.submission_template}")
    print(json.dumps({"cases": len(cases), "prompt_dirs": len(index)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
