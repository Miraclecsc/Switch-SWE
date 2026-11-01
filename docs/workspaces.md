# Preparing public source workspaces

This tool prepares the initial source files for every workspace in one released
case. It is a public source preparer, not a complete evaluation runner. It does not
include private tests, scoring, runtime images, dependency installations, model
execution, or validated per-case environments. Tracked public tests may be present
in the selected source snapshot; their presence does not provide private evaluation
coverage or establish that the task can run in your environment.

The release contains 200 pairs / 400 condition-specific cases. Select the exact
`case_id` from `data/cases.json`. The preparer reads the frozen JSON without
rewriting it and creates all entries in the selected case's `workspaces` list.
It does not interpret or execute `turns`.

## Requirements and inputs

Use Linux with Python 3.10 or later, Git on the system path, and libc `renameat2`
support. Python code uses only the standard library. Git must support
`--initial-branch` and `--object-format` (Git 2.29 or later).
The CLI runs directly from the checkout; no Python package installation is needed.

The data directory, by default this checkout's `data/`, must contain:

- `cases.json`: the frozen list of cases, including `case_id`, `pair_id`,
  `condition`, `workspaces` and `turns`. Each workspace declares `workspace`,
  `repo` (`owner/repo`) and a full lowercase `commit` ID.
- `workspace_overlays.json`: a map of `case_id` → workspace name → relative source
  path → overlay or `null`. Every workspace must have an explicit map; use `{}`
  when there are no overlays. A missing map is an error.
- `blobs/<sha256>`: public initial source bytes referenced by overlays.
  Each non-null overlay has `mode`, `sha256`, and `content_path`, where
  `content_path` is exactly `blobs/<sha256>`. Modes are `100644` (file),
  `100755` (executable file), and `120000` (symlink target bytes).
  `null` deletes a path and its descendants.

Prepare trusted bare repositories separately at
`REPO_CACHE/<owner>/<repo>.git`. Each must already contain the requested commit
and its complete tree and blobs. A missing or incomplete cache fails; the preparer
does not clone, fetch, initialize submodules, or download Git LFS content.
LFS pointers remain the committed pointer bytes.

## Preview and prepare

From the release root, set `CASE_ID` to an exact released ID and use a new output
directory for each preparation:

```bash
CASE_ID=sf001_switched  # Replace with an ID from data/cases.json.
REPO_CACHE=/path/to/repo-cache
CASE_OUTPUT=/path/to/prepared-case

python3 scripts/prepare_workspaces.py \
  --case-id "$CASE_ID" --repo-cache "$REPO_CACHE" \
  --out-dir "$CASE_OUTPUT" --dry-run
```

Dry-run prints JSON listing every workspace, repository, commit, cache path,
overlay counts and manual `git clone --bare` preparation commands. Repositories
are deduplicated in the requirements list. The commands are suggestions for
GitHub `owner/repo` repositories and are never executed. Only use a clone command
when its destination does not exist. A normal clone may not contain an unadvertised
commit; acquiring that commit is a separate cache preparation step.

Dry-run reads and validates the selected metadata, but does not create any files,
invoke Git, verify cached object availability, or hash blob contents. Its
`cache_exists` field only means the cache directory exists. Preparation performs
the actual bare repository, object and byte checks.

After preparing the required caches, ensure the output's parent exists:

```bash
mkdir -p "$(dirname "$CASE_OUTPUT")"
python3 scripts/prepare_workspaces.py \
  --case-id "$CASE_ID" --repo-cache "$REPO_CACHE" \
  --out-dir "$CASE_OUTPUT"
```

Use `--data-dir /path/to/data` to read another export with the same schema.
Input and output paths must not contain symlinks. Output must be outside the
cache and data directories. An existing output is refused, including an empty
directory or symlink; choose a fresh path to preserve previous work.

The result is `CASE_OUTPUT/<workspace>/` for each declared workspace. Standard
output is a JSON summary with final paths, file and byte counts and synthetic
commit IDs. Errors return exit status 2. Reports are not written into workspaces.
All workspaces are staged together and published atomically without replacing
an existing output. Failure in any workspace removes the staging directory and
leaves the requested output absent; a concurrent writer's output is preserved.

## Snapshot and history isolation

`src/switch_swe/materialize.py` and its regression tests are ported from
SessionSwitchBench's `src/driver/independent_v1/materialize.py` and
`test_materialize.py`. The original snapshot, audit and synthetic Git
implementation is retained. The wrapper adds public data loading and publication
of the complete case.

The materializer reads the chosen commit through a temporary object-store facade,
applies the declared initial overlays, verifies file bytes and modes, and constructs
a new Git repository in each workspace. Git export attributes, filters, EOL
conversion, templates and inherited caller Git settings do not change source bytes.
Source cache contents and modification times are preserved.

Each workspace has exactly one synthetic initial commit, a clean working tree,
no upstream remotes, no alternate object store, and no inherited history.
All stored Git objects must be reachable from that initial commit. Successor
commits, unrelated source blobs, source author metadata and upstream refs are
not copied into the resulting Git repository. The two workspaces remain independent
even when their repository and base commit match.

Nested Git metadata and Git submodule entries are stripped. Unsafe paths, escaping
or cyclic symlinks, unsupported modes, missing blobs and digest mismatches fail
closed. Safe symlink target bytes and executable modes are preserved. Later source
states are not selected from `turns`; only the declared initial commit and public
initial overlays are materialized.

This is a source and Git-history isolation guarantee, not a process sandbox.
Keep the source caches and unrelated host files outside any agent-visible
environment. Restrict agent filesystem and network access separately when running
an evaluation; this tool does not configure either. Its success also does not
certify that release metadata or selected initial source content are free of
semantic benchmark leakage.

## Local verification

The tests construct small temporary Git repositories and use no model service or
downloaded repository:

```bash
python3 -B -m unittest discover -s tests -p 'test_materialize.py' -v
python3 -B -m unittest discover -s tests -p 'test_prepare_workspaces.py' -v
```

They check binary and CRLF byte preservation, deletions, modes, symlinks, raw Git
attributes, absence of inherited or future objects, independent workspace edits,
cache preservation, dry-run behavior, corrupt hashes, missing inputs, and refusal
to reuse an output.

## Real released-case verification: November 1, 2026

The public CLI materialized the final released `sf076_switched` case using
Python 3.10.20 on Linux and a local `git clone --bare --shared` cache for
`pypa/packaging`. All five workspaces passed independent verification:
482 files matched the expected paths, contents and modes; all five overlay writes
matched the public blobs byte-for-byte and by SHA-256. Each workspace had exactly
one commit under both `HEAD` and `--all`, a clean working tree, no remotes or
alternates, and no extra Git objects. The original bare cache's content and
modification-time fingerprints were unchanged.

The output, `preparation.json`, and `verification.json` (including actual commands
and per-workspace results) are preserved under
`/mnt/jfs/mengziyang/changshuochen/SessionSwitchBench/workspaces/switch-swe-public-verification-20261101/`.
This was one source-preparation check; no model, dependency installation, test
suite rerun, or evaluation runtime was involved.
