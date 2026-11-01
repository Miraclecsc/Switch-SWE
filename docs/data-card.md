# Data card

## Release identity

Switch-SWE is the public packaging of the frozen `fixed200-v1` cohort previously
developed under the name SessionSwitchBench. The prompt revision is
`inplace-clarification-20260916`, resealed on September 16, 2026 at 08:20:56 UTC.
`data/cases.json` preserves the original `effective-cases.json` **byte for byte**.

| Property | Value |
| --- | ---: |
| Focus tasks / matched pairs | 200 |
| Near pairs (historical T4) | 100 |
| Far pairs (historical T3) | 100 |
| Baseline sessions | 200 |
| Switched sessions | 200 |
| Repositories | 19 |
| Requests across baseline sessions, including finalization | 1,137 |
| Requests across switched sessions, including finalization | 4,513 |
| Interruption requests | 3,376 |
| Distinct initial-source overlay blobs | 856 |

The two locality groups contain different focus tasks. Each focus task has a
baseline and a switched session; it does not have both near and far variants.
`far` is the release's name, not `fast`.

## Files and fields

`data/pairs.json` is the 200-row entry point. Each row identifies its split,
historical tier, focus task ID, repository, original base commit, paired case
IDs, and frozen source version. `data/splits/{near,far}.json` contains ordered
pair IDs.

`data/cases.json` contains 400 sessions:

| Field | Meaning |
| --- | --- |
| `case_id` | Execution arm, e.g. `sf001_switched` |
| `pair_id` | Shared target identity, e.g. `sf001` |
| `condition` | `baseline` or `switched` |
| `tier` | Baseline: 0; switched: 4 near / 3 far |
| `task_id` | Internal frozen focus task identifier |
| `focus_workspace` | Controller's focus checkout |
| `workspaces` | Checkout names, repositories and pinned base commits |
| `turns` | Ordered requests with `index`, `role`, `source_label`, `workspace`, `prompt` |
| `prompt_style` | Historical construction label, retained without reinterpretation |

`A_final` is the final focus request. The opaque `task_id` required in its JSON
answer may differ from the case-level task ID; adapters must follow the prompt.
Metadata such as role, tier, source label and workspace assignment belongs to
the controller and must not be added to model prompts.

`data/workspace_overlays.json` maps case → workspace → relative file path →
initial file descriptor. A descriptor records its Git mode, SHA-256 and
`content_path`; `null` deletes a path. Blob bytes are in `data/blobs/`. These
files reproduce the initial checkout, including source-history adjustments.
They are not a set of reference solutions for the target.

`data/provenance.json` binds each pair to its original source version and hashes.
`release_manifest.json` hashes every data file, including all blobs.

## Construction and locality

The tasks adapt repository repair instances and development records into staged
requests. The authors also added follow-up requirements and regression tests.
Preserved source records do not imply that every request is a verbatim upstream
review comment. Development included model-informed revisions and selection;
this cohort should not be described as an outcome-blind random sample.

Let `C(t)` be the source files modified by a task's reference fix, excluding
tests and documentation, and `D(t)` their immediate parent directories. The
construction rule for a focus task `f` and interruption `b` is:

| Group | Rule |
| --- | --- |
| Near (T4) | `C(f) ∩ C(b) = ∅` and `D(f) ∩ D(b) ≠ ∅` |
| Far (T3) | `C(f) ∩ C(b) = ∅` and `D(f) ∩ D(b) = ∅` |

All five tasks in a switched session belong to the same repository, with
separate persistent checkouts at their respective base commits. Directory
overlap is an operational proxy for locality, not a semantic similarity score.
The historical audit records a shared-parent-directory exception for `sf073`
in the far group. Its frozen label is preserved.

## Matched-control limitations

The frozen cohort contains historical exceptions to the idealized design.
The September 25 appendix audit reports:

- Nonfinal focus payloads match in 199/200 pairs.
- Including finalization, complete focus request sequences match in 72/200.
  The September 16 revision added natural-language target references to some
  switched final requests.
- Nonfinal focus request counts range from 2 to 8; 29 pairs have only 2.
- Every interruption appears in at least two chunks in 137/200 switched sessions.
- Finalization immediately follows a nonfinal focus request in 95/200 sessions.

The release preserves these cases. It does not silently regenerate prompts or
relabel membership to fit a cleaner description. The verification script checks
frozen integrity and structural consistency; it does not certify all locality
rules from private reference fixes.

## Scope and licensing

This package contains prompts, initial-source overlays, split membership and
source preparation tools. It does not include private test patches, reference
solutions, private test selectors, compiled dependency caches or runtime images.
Existing historical environment qualification is not a fresh test run of this
public package. See [the evaluation protocol](evaluation.md).

Repository code and source-derived blobs retain their upstream licenses.
The root MIT license applies to original project code; it does not relicense
third-party material. Preserve upstream license and copyright notices when
preparing or redistributing checkouts. See [third-party notices](../THIRD_PARTY_NOTICES.md).
