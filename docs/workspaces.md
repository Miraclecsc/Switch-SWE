# Preparing workspaces

Use Linux, Python 3.10+, Git 2.29+ and libc with `renameat2`. The preparer applies each case's initial source changes and creates an independent checkout for every task.

## Prepare a case

Store bare repositories at `REPO_CACHE/<owner>/<repo>.git`. Preview the required commits and clone commands:

```sh
python3 scripts/prepare_workspaces.py \
  --case-id sf001_switched \
  --repo-cache /path/to/repo-cache \
  --out-dir /path/to/new-case \
  --dry-run
```

Run the printed clone commands, create the output's parent directory, then repeat without `--dry-run`. Use a new output path for each case. Each cached repository must contain the requested commits and source objects. Use regular paths without symlink components for the cache, data and output directories.

The output contains `w00/` for a baseline, or `w00/` through `w04/` for a switched session. Each checkout has one synthetic initial Git commit. Mount these directories at `/work/w00`, etc. when running the frozen prompts.

The command prepares source files. Install task dependencies separately; grading uses the separately maintained evaluation runtime and tests.

## Input format

- `cases.json`: case IDs, workspace names, repositories and commits.
- `workspace_overlays.json`: case → workspace → file changes.
- `blobs/<sha256>`: file contents referenced by those changes.

Each file descriptor records `mode`, `sha256` and `content_path`. Modes are `100644`, `100755` and `120000`; `null` removes a path. Use `--data-dir` to select a different data directory.

The materializer is ported from the original SessionSwitchBench implementation. It preserves file bytes, executable modes and symlinks while giving each task its own initial Git history.

## Verification

```sh
python3 -B -m unittest discover -s tests -p 'test_materialize.py'
python3 -B -m unittest discover -s tests -p 'test_prepare_workspaces.py'
```

On November 1, 2026, the released `sf076_switched` case was prepared with Python 3.10.20. All five packaging checkouts passed: 482 files, five initial file changes, and one Git commit per checkout. See the [validation record](validation.md).
