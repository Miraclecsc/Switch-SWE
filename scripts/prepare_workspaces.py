#!/usr/bin/env python3
"""Prepare every independent source workspace for one released Switch-SWE case."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from switch_swe.materialize import (  # noqa: E402
    MaterializeError,
    canonical_host,
    load_json,
    materialize,
    metadata,
    normalize_overrides,
    object_id,
    publish,
    relative,
    require,
)

COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")


def component(value):
    require(isinstance(value, str) and COMPONENT.fullmatch(value) and not metadata(value),
            "Expected a simple workspace or repository name")
    return value


def case_inputs(data_dir, case_id, repo_cache):
    """Read release inputs without rewriting frozen case or overlay data."""
    data_dir = canonical_host(data_dir)
    repo_cache = canonical_host(repo_cache)
    cases = load_json(data_dir / "cases.json")
    require(isinstance(cases, list), "cases.json must be a list")
    by_id = {}
    for case in cases:
        require(isinstance(case, dict) and isinstance(case.get("case_id"), str),
                "Every case needs a case_id")
        require(case["case_id"] not in by_id, "Duplicate case_id")
        by_id[case["case_id"]] = case
    require(case_id in by_id, f"Unknown case_id: {case_id}")
    case = by_id[case_id]
    workspaces = case.get("workspaces")
    require(isinstance(workspaces, list) and workspaces, "Case needs workspaces")
    all_overlays = load_json(data_dir / "workspace_overlays.json")
    require(isinstance(all_overlays, dict) and case_id in all_overlays,
            "Missing overlays for selected case (use explicit empty workspace maps)")
    overlays = all_overlays[case_id]
    require(isinstance(overlays, dict), "Case overlays must be a workspace map")
    rows, names = [], set()
    for workspace in workspaces:
        require(isinstance(workspace, dict), "Workspace must be an object")
        name = component(workspace.get("workspace"))
        require(name not in names, "Duplicate workspace name")
        names.add(name)
        repo = relative(workspace.get("repo"))
        parts = repo.split("/")
        require(len(parts) == 2, "Repository must be owner/repo")
        owner, project = map(component, parts)
        commit = object_id(workspace.get("commit"))
        require(name in overlays and isinstance(overlays[name], dict),
                f"Missing overlay map for workspace: {name}")
        changes = normalize_overrides(overlays[name])
        for value in changes.values():
            if value is not None:
                require(set(value) == {"mode", "sha256", "content_path"},
                        "Public overlays require mode, sha256 and content_path")
                require(value["content_path"] == "blobs/" + value["sha256"],
                        "Public overlay content_path must be blobs/<sha256>")
        rows.append({
            "workspace": name,
            "repo": repo,
            "commit": commit,
            "cache_path": str(canonical_host(repo_cache / owner / (project + ".git"))),
            "overlays": changes,
        })
    require(set(overlays) == names, "Overlay workspace names differ from selected case")
    return rows


def preparation_plan(case_id, rows, out_dir):
    """Describe requirements, including manual clone commands; never run them."""
    repositories = {}
    workspaces = []
    for row in rows:
        cache_path = Path(row["cache_path"])
        repository = repositories.setdefault(row["repo"], {
            "repo": row["repo"],
            "cache_path": str(cache_path),
            "cache_exists": cache_path.is_dir(),
            "commits": [],
            "clone_command": (
                shlex.join(["mkdir", "-p", "--", str(cache_path.parent)])
                + " && "
                + shlex.join(["git", "clone", "--bare", "--",
                              f"https://github.com/{row['repo']}.git", str(cache_path)])
            ),
        })
        if row["commit"] not in repository["commits"]:
            repository["commits"].append(row["commit"])
        workspaces.append({
            key: row[key] for key in ("workspace", "repo", "commit", "cache_path")
        } | {
            "path": str(out_dir / row["workspace"]),
            "overlay_writes": sum(value is not None for value in row["overlays"].values()),
            "overlay_deletions": sum(value is None for value in row["overlays"].values()),
        })
    return {"case_id": case_id, "out_dir": str(out_dir),
            "repositories": list(repositories.values()), "workspaces": workspaces}


def prepare_case(case_id, repo_cache, out_dir, *, data_dir=ROOT / "data", dry_run=False):
    """Atomically publish all case workspaces, with a separate synthetic Git per workspace."""
    rows = case_inputs(data_dir, case_id, repo_cache)
    out_dir = canonical_host(out_dir)
    for input_root in (repo_cache, data_dir):
        require(not out_dir.is_relative_to(canonical_host(input_root)),
                "Output must be outside repository cache and release data")
    require(not os.path.lexists(out_dir), "Output exists; choose a new out-dir")
    plan = preparation_plan(case_id, rows, out_dir)
    if dry_run:
        return {"dry_run": True, **plan}
    require(out_dir.parent.is_dir(), "Output parent must already exist")
    missing = [r["cache_path"] for r in plan["repositories"] if not r["cache_exists"]]
    require(not missing, "Missing bare repository cache: " + ", ".join(missing)
            + "; use --dry-run to print manual clone commands")
    reports = []
    with tempfile.TemporaryDirectory(prefix=".prepare-workspaces-", dir=out_dir.parent) as tmp:
        stage = Path(tmp) / "case"
        stage.mkdir(mode=0o755)
        stage.chmod(0o755)
        for row in rows:
            report = materialize(
                row["cache_path"], row["commit"], row["overlays"],
                stage / row["workspace"], overlay_root=data_dir,
            )
            reports.append({
                "workspace": row["workspace"],
                "path": str(out_dir / row["workspace"]),
                "repo": row["repo"],
                "commit": row["commit"],
                **{key: report[key] for key in ("files", "bytes", "synthetic_commit")},
            })
        publish(stage, out_dir)
    return {"case_id": case_id, "out_dir": str(out_dir), "workspaces": reports}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--repo-cache", required=True,
                        help="Existing bare repositories at CACHE/owner/repo.git")
    parser.add_argument("--out-dir", required=True,
                        help="New case directory; parent must exist when preparing")
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print requirements and manual clone commands without writing or cloning")
    args = parser.parse_args(argv)
    try:
        result = prepare_case(args.case_id, args.repo_cache, args.out_dir,
                              data_dir=args.data_dir, dry_run=args.dry_run)
    except (MaterializeError, OSError, ValueError) as exc:
        parser.exit(2, f"prepare_workspaces: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
