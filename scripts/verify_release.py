#!/usr/bin/env python3
"""Check frozen identity, split membership, session structure and source blobs."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

CASE_SHA256 = "a47fefc8d3fc7251a25a56c74e5dd56637c7507cde1bcb085d921cf47d77da86"
ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(value):
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and not PurePosixPath(value).is_absolute()
            and all(p not in {"", ".", "..", ".git"} for p in value.split("/")))


def verify(root):
    errors = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    manifest = load(root / "release_manifest.json")
    data = root / "data"
    cases = load(data / "cases.json")
    pairs = load(data / "pairs.json")
    overlays = load(data / "workspace_overlays.json")
    check(sha(data / "cases.json") == CASE_SHA256, "Frozen case bytes changed")
    actual_files = {str(p.relative_to(root)) for p in data.rglob("*") if p.is_file()}
    check(actual_files == set(manifest["files"]), "Data file inventory differs from manifest")
    for name, expected in manifest["files"].items():
        if not safe_path(name):
            errors.append(f"Invalid manifest path: {name}")
            continue
        path = root / name
        check(path.is_file() and not path.is_symlink() and sha(path) == expected,
              f"Checksum mismatch: {name}")
    by_id = {c["case_id"]: c for c in cases}
    check(len(cases) == len(by_id) == 400, "Expected 400 unique case IDs")
    pair_ids = {p["pair_id"] for p in pairs}
    check(len(pairs) == len(pair_ids) == 200, "Expected 200 unique pairs")
    check(len({p["task_id"] for p in pairs}) == 200, "Focus task IDs must be unique")
    check(Counter(p["split"] for p in pairs) == {"near": 100, "far": 100},
          "Expected 100 near / 100 far")
    check(set(overlays) == set(by_id), "Overlay coverage differs from case coverage")
    for split in ("near", "far"):
        check(load(data / "splits" / f"{split}.json")
              == [p["pair_id"] for p in pairs if p["split"] == split],
              f"{split} split index differs")
    for pair in pairs:
        pid = pair["pair_id"]
        check(pair["split"] == {3: "far", 4: "near"}.get(pair["tier"]),
              f"{pid}: incorrect split/tier mapping")
        for condition in ("baseline", "switched"):
            cid = pair[f"{condition}_case_id"]
            case = by_id.get(cid)
            if not case:
                errors.append(f"{pid}: missing {condition}")
                continue
            check(case["pair_id"] == pid and case["condition"] == condition,
                  f"{cid}: pair/condition mismatch")
            check(case["task_id"] == pair["task_id"], f"{cid}: task ID mismatch")
            check(case["tier"] == (0 if condition == "baseline" else pair["tier"]),
                  f"{cid}: tier mismatch")
            workspaces = {w["workspace"]: w for w in case["workspaces"]}
            check(len(workspaces) == len(case["workspaces"]) == (1 if condition == "baseline" else 5),
                  f"{cid}: incorrect workspace count")
            check(set(overlays.get(cid, {})) == set(workspaces), f"{cid}: missing workspace overlays")
            check({w["repo"] for w in workspaces.values()} == {pair["repository"]},
                  f"{cid}: repository mismatch")
            focus = workspaces.get(case["focus_workspace"], {})
            check(focus.get("commit") == pair["base_commit"], f"{cid}: focus base mismatch")
            for workspace, spec in workspaces.items():
                check(re.fullmatch(r"[0-9a-f]{40}", spec["commit"]) is not None,
                      f"{cid}/{workspace}: invalid base commit")
            turns = case["turns"]
            check(bool(turns), f"{cid}: empty turns")
            check([t["index"] for t in turns] == list(range(len(turns))), f"{cid}: unordered turns")
            if turns:
                check(turns[-1]["source_label"] == "A_final"
                      and turns[-1]["role"] == "focus"
                      and turns[-1]["workspace"] == case["focus_workspace"],
                      f"{cid}: invalid final focus request")
            check(sum(t["source_label"] == "A_final" for t in turns) == 1,
                  f"{cid}: expected exactly one final request")
            for turn in turns:
                check(turn["workspace"] in workspaces, f"{cid}: unknown turn workspace")
                check(isinstance(turn["prompt"], str) and bool(turn["prompt"].strip()),
                      f"{cid}: missing prompt")
                check(turn["role"] in {"focus", "interruption"}, f"{cid}: invalid role")
                if condition == "baseline":
                    check(turn["role"] == "focus", f"{cid}: interrupted baseline")
    referenced = set()
    for cid, workspaces in overlays.items():
        for workspace, files in workspaces.items():
            for name, value in files.items():
                check(safe_path(name), f"{cid}/{workspace}: unsafe overlay path")
                if value is None:
                    continue
                check(value.get("mode") in {"100644", "100755", "120000"},
                      f"{cid}/{workspace}: invalid overlay mode")
                digest = value.get("sha256", "")
                if not re.fullmatch(r"[0-9a-f]{64}", digest):
                    errors.append("Invalid blob digest")
                    continue
                check(value.get("content_path") == f"blobs/{digest}", "Invalid blob path")
                referenced.add(digest)
    check(referenced == {p.name for p in (data / "blobs").iterdir()}, "Blob coverage differs")
    for digest in referenced:
        path = data / "blobs" / digest
        check(path.is_file() and sha(path) == digest, f"Blob bytes differ: {digest}")
    check(manifest["pairs"] == len(pairs) and manifest["cases"] == len(cases),
          "Manifest counts differ")
    check(manifest["source_case_sha256"] == CASE_SHA256, "Manifest source identity differs")
    check(manifest["repositories"] == len({p["repository"] for p in pairs}),
          "Manifest repository count differs")
    check(manifest["initial_source_blobs"] == len(referenced), "Manifest blob count differs")
    return {
        "status": "pass" if not errors else "fail",
        "pairs": len(pairs),
        "cases": len(cases),
        "splits": dict(Counter(p["split"] for p in pairs)),
        "repositories": len({p["repository"] for p in pairs}),
        "source_blobs": len(referenced),
        "source_case_sha256": CASE_SHA256,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        report = verify(args.root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"status": "fail", "errors": [str(exc)]}
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
