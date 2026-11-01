#!/usr/bin/env python3
"""List benchmark pairs or inspect a case. This is a controller-side tool."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--split", choices=["near", "far"])
    parser.add_argument("--case-id")
    parser.add_argument("--turn", type=int, help="Print exactly this zero-based prompt, without metadata")
    parser.add_argument("--json", action="store_true", help="Print full case JSON (controller only)")
    args = parser.parse_args()
    pairs = json.loads((args.data_dir / "pairs.json").read_text())
    if not args.case_id:
        if args.turn is not None or args.json:
            parser.error("--turn and --json require --case-id")
        print("PAIR    SPLIT  REPOSITORY")
        for pair in pairs:
            if args.split is None or pair["split"] == args.split:
                print(f"{pair['pair_id']:7} {pair['split']:6} {pair['repository']}")
        return
    cases = json.loads((args.data_dir / "cases.json").read_text())
    case = next((c for c in cases if c["case_id"] == args.case_id), None)
    if case is None:
        parser.error(f"Unknown case: {args.case_id}")
    if args.turn is not None:
        if not 0 <= args.turn < len(case["turns"]):
            parser.error(f"--turn must be between 0 and {len(case['turns']) - 1}")
        print(case["turns"][args.turn]["prompt"])
    elif args.json:
        print(json.dumps(case, ensure_ascii=False, indent=2))
    else:
        pair = next(p for p in pairs if p["pair_id"] == case["pair_id"])
        print(f"{case['case_id']} | {pair['split']} | {pair['repository']}")
        print(f"{len(case['workspaces'])} workspaces; {len(case['turns'])} turns")
        print("Controller metadata below must not be supplied to the agent.")
        for turn in case["turns"]:
            print(f"{turn['index']:2}  {turn['source_label']:8}  {turn['workspace']}  "
                  f"{turn['prompt'].splitlines()[0][:110]}")


if __name__ == "__main__":
    main()
