#!/usr/bin/env python3
"""Demo scorer for SessionSwitchBench submissions.

This is intentionally lightweight and public. It checks that a submitted final
patch is a non-empty unified diff and writes a JSON result. It is not the hidden
leaderboard scorer and does not run held-out tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def is_unified_diff(text: str) -> bool:
    return bool(text.strip()) and "diff --git " in text and "--- " in text and "+++ " in text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    row = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    patch = str(row.get("patch") or "")
    result = {
        "case_id": row.get("case_id"),
        "task_id": row.get("task_id"),
        "demo_valid_unified_diff": is_unified_diff(patch),
        "patch_bytes": len(patch.encode("utf-8")),
        "note": "Demo-only format check. Official scoring uses executable tests.",
    }
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["demo_valid_unified_diff"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
