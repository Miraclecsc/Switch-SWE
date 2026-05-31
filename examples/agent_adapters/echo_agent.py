#!/usr/bin/env python3
"""Minimal answer-agent adapter used for harness smoke tests.

Real evaluations should replace this command with a Codex, Claude Code, or other
agent CLI wrapper. The script reads the current turn prompt from stdin and emits
an empty final patch only when the controller marks the turn as scored.
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    _prompt = sys.stdin.read()
    if os.environ.get("SSB_TURN_SCORED") == "true":
        print(
            json.dumps(
                {
                    "task_id": os.environ.get("SSB_FOCUS_TASK_ID"),
                    "subtask_id": os.environ.get("SSB_TURN_STAGE_ID"),
                    "analysis": "Echo adapter smoke test; no repair attempted.",
                    "files": [],
                    "patch": "",
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
