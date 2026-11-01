#!/usr/bin/env python3
"""Export the frozen fixed200 release without changing its case bytes."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil

CASE_SHA256 = "a47fefc8d3fc7251a25a56c74e5dd56637c7507cde1bcb085d921cf47d77da86"
TIER_SPLITS = {4: "near", 3: "far"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def checked(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Source hash mismatch: {path}")
    return data


def collect_pair(row):
    root = Path(row["source_release"])
    raw = checked(root / "private/workspace-overlays.json",
                  row["bindings"]["private/workspace-overlays.json"])
    overlays = json.loads(raw)
    if set(overlays) != set(row["case_ids"]):
        raise ValueError(f"Overlay case scope mismatch: {row['pair_id']}")
    blobs = {}
    for workspaces in overlays.values():
        for files in workspaces.values():
            for value in files.values():
                if value is None:
                    continue
                if set(value) != {"mode", "sha256", "content_path"}:
                    raise ValueError(f"Unsupported frozen overlay: {row['pair_id']}")
                sha = value["sha256"]
                source = (root / value["content_path"]).resolve()
                if not source.is_relative_to(root.resolve()):
                    raise ValueError("Overlay source escapes release")
                blobs[sha] = source
                value["content_path"] = f"blobs/{sha}"
    provenance = {
        "pair_id": row["pair_id"],
        "source_version": row["source_version"],
        "source_bindings": row["bindings"],
    }
    return overlays, blobs, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Original releases/fixed200-v1 directory")
    parser.add_argument("--out", type=Path, required=True, help="New, empty release directory")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must not exist")
    release_raw = (args.source / "release.json").read_bytes()
    release = json.loads(release_raw)
    cases_raw = checked(args.source / release["entry"], CASE_SHA256)
    if release["files"][release["entry"]] != CASE_SHA256:
        raise ValueError("Frozen release identity mismatch")
    cohort_raw = checked(args.source / "cohort.json", release["files"]["cohort.json"])
    cohort = json.loads(cohort_raw)
    cases = json.loads(cases_raw)
    switched = {c["pair_id"]: c for c in cases if c["condition"] == "switched"}
    if len(cases) != 400 or len(switched) != 200 or len(cohort["pairs"]) != 200:
        raise ValueError("Expected exactly 200 pairs / 400 cases")
    with ThreadPoolExecutor(max_workers=8) as pool:
        collected = list(pool.map(collect_pair, cohort["pairs"]))
    overlays, blobs, provenance = {}, {}, []
    for mapping, sources, evidence in collected:
        if overlays.keys() & mapping.keys():
            raise ValueError("Duplicate case overlays")
        overlays.update(mapping)
        blobs.update(sources)
        provenance.append(evidence)
    if set(overlays) != {c["case_id"] for c in cases}:
        raise ValueError("Overlay scope differs from frozen cases")
    pairs = []
    for row in cohort["pairs"]:
        case = switched[row["pair_id"]]
        focus = next(w for w in case["workspaces"] if w["workspace"] == case["focus_workspace"])
        pairs.append({
            "pair_id": row["pair_id"],
            "split": TIER_SPLITS[case["tier"]],
            "tier": case["tier"],
            "task_id": case["task_id"],
            "repository": focus["repo"],
            "base_commit": focus["commit"],
            "baseline_case_id": f"{row['pair_id']}_baseline",
            "switched_case_id": f"{row['pair_id']}_switched",
            "source_version": row["source_version"],
        })
    if Counter(p["split"] for p in pairs) != {"near": 100, "far": 100}:
        raise ValueError("Expected 100 near / 100 far")
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda item: checked(item[1], item[0]), blobs.items()))
    args.out.mkdir(parents=True)
    data = args.out / "data"
    (data / "blobs").mkdir(parents=True)
    (data / "cases.json").write_bytes(cases_raw)
    write_json(data / "pairs.json", pairs)
    write_json(data / "workspace_overlays.json", overlays)
    for sha, source in blobs.items():
        shutil.copyfile(source, data / "blobs" / sha)
    for split in ("near", "far"):
        write_json(data / "splits" / f"{split}.json",
                   [p["pair_id"] for p in pairs if p["split"] == split])
    write_json(data / "provenance.json", {
        "source_release": release["release_id"],
        "prompt_revision": release["prompt_revision"],
        "source_release_sha256": digest(release_raw),
        "source_cohort_sha256": digest(cohort_raw),
        "source_cases_sha256": CASE_SHA256,
        "resealed_at_utc": release["resealed_at_utc"],
        "transformations": [
            "effective-cases.json copied byte-for-byte to data/cases.json",
            "pair index and near/far membership derived from frozen cohort and tiers",
            "workspace overlays merged; blob content paths normalized to blobs/<sha256>",
            "only initial-checkout blobs copied; no scoring payloads or model outputs",
        ],
        "pairs": provenance,
    })
    files = {str(p.relative_to(args.out)): digest(p.read_bytes())
             for p in sorted(data.rglob("*")) if p.is_file()}
    manifest = {
        "benchmark": "Switch-SWE",
        "release": "fixed200-v1-public",
        "prompt_revision": release["prompt_revision"],
        "pairs": 200,
        "cases": 400,
        "splits": {"near": 100, "far": 100},
        "tier_mapping": {"4": "near", "3": "far"},
        "repositories": len({p["repository"] for p in pairs}),
        "baseline_sessions": 200,
        "switched_sessions": 200,
        "initial_source_blobs": len(blobs),
        "source_case_sha256": CASE_SHA256,
        "includes_private_scorer": False,
        "includes_runtime_bundles": False,
        "files": files,
    }
    write_json(args.out / "release_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
