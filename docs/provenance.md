# Release provenance

This repository replaces the original 500-task draft with the final 200-pair
cohort. The old draft remains in Git commit `e7d4db8`.

## Frozen inputs

The source directory inspected on November 1, 2026 was:

```text
/mnt/jfs/mengziyang/changshuochen/SessionSwitchBench/
  workspaces/SessionSwitchBench/releases/fixed200-v1/
```

| Source file | SHA-256 |
| --- | --- |
| `effective-cases.json` | `a47fefc8d3fc7251a25a56c74e5dd56637c7507cde1bcb085d921cf47d77da86` |
| `cohort.json` | `08476295333604ac88674ca3845c1f311e53d7158fea844ab719912bbaa14dab` |
| `prompt-clarification.json` | `997904c2ee738d7ff75c4679813e54d2674c759e2d305f31f54f918cf19447ec` |

The effective case hash also matched all 18 inspected copies in subsequent
Claude, Gemini, GLM, Kimi, Codex and continuation worktrees. The revision is
`inplace-clarification-20260916`; the source release was resealed at
`2026-09-16T08:20:56.258010+00:00`.

The source `cohort.json` selects each pair's exact candidate version. All 200
selected `private/workspace-overlays.json` files matched their cohort bindings.
Only blobs referenced by these initial overlays were exported: 856 distinct
files totaling 38,201,738 bytes.

Although the original overlay manifest lived under a directory called
`private`, its referenced bytes are part of the initial agent-visible checkout.
The public manifest normalizes blob paths and retains file bytes, modes and
deletions. `data/provenance.json` records the original source-binding hashes;
`release_manifest.json` records the hashes of the exported representation.

## Rebuilding the export

The maintainer importer requires the original frozen directory and the source
assets referenced by its cohort. Choose a new output directory:

```sh
python3 scripts/import_frozen_release.py \
  --source /path/to/original/releases/fixed200-v1 \
  --out /path/to/new-export
python3 scripts/verify_release.py --root /path/to/new-export
```

## Paper material used

The README and documentation synthesize local manuscript and audit material:

| Material | Use |
| --- | --- |
| `/data/coding_iclr/iclr2027_conference.tex` | Motivation and locality construction |
| `private/history-construction-provenance-20260925/AUDIT.md` | Source records versus authored follow-ups |
| `private/paper-appendix-refine-20260925/compiled-text.txt` | Corrected protocol, resources and frozen-data exceptions |
| `private/history-head-to-head-gap-20260925-v1/resolution-report.md` | Historical result coverage |
| `private/history-workload-table-v1/README.md` | Resource metric definitions |
| `private/rcm-figure-refine-20260926/refined-v2.png` | RCM method illustration copied to `docs/assets/rcm.png` |

The `private/` paths above are relative to the original SessionSwitchBench
archive. They record the manuscript and experiment sources used for this release.

The OpenCode plugin has its own [source and byte-level provenance](../plugins/context-manager/PROVENANCE.json)
and [validation record](../plugins/context-manager/VALIDATION.md).
