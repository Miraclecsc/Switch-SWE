# Benchmark Construction

This document describes the v1 construction pipeline at the level needed to
understand and reproduce the public benchmark format. Private validation
artifacts are intentionally not included in this public repository.

## 1. Source Task Pool

SessionSwitchBench v1 starts from SWE-bench-family repository repair tasks. In
the private construction index, each original task has:

- an original repair-task id;
- a repository name;
- a base commit;
- an issue statement;
- private executable evaluation material.

The public v1 release contains 500 selected tasks covering 410 repositories.
Public task ids are anonymized as `ssb_v1_task_0001`, etc.

The private construction index records these source labels:

| Source label | Tasks |
| --- | ---: |
| `SWE-bench-extra` | 372 |
| `SWE-bench_Verified` | 52 |
| `SWE-bench-dev` | 43 |
| `SWE-bench-Live` | 21 |
| `SWE-bench_Lite` | 6 |
| `SWE-bench` | 6 |

These labels describe the internal source pool. The public repository does not
ship original ids or source labels as agent-facing inputs.

## 2. Strict Executable Filtering

Tasks were selected from an internal strict executable pool. A task entered that
pool only after internal validation that the repository can be checked out at
the base commit and that the held-out patch-scoring path is executable.

The private scorer keeps the evaluation material required for this step. The
public repository does not include reference patches, test patches,
fail-to-pass/pass-to-pass metadata, or environment recipes.

## 3. Workflow-Stage Decomposition

Each selected repair task was converted into a task-specific workflow of 3--6
coding-agent stages. The stages are designed as incremental work steps, not as
separate independent tasks.

The public task metadata records only:

- `stage_id`;
- a short stage title;
- whether that stage expects the final patch.

Agent-facing prompts are generated from these stages. The first stage provides
the issue and repository routing information. Later stages are resume prompts
that rely on the same case session for earlier context. The final stage requires
a strict JSON response containing a standalone unified diff in `patch`.

During construction, prompt text was cleaned to remove:

- target areas;
- known failing tests;
- must-keep passing tests;
- reference/test/gold patch language;
- hidden/oracle/private scorer language;
- direct answer-like wording where possible.

## 4. Session Case Construction

Each of the 500 public tasks is the unique focus task of exactly one switched
case and one matched focus-control case.

A switched case interleaves the focus task with several interruption tasks:

- the focus task appears within the first three turns;
- every task's internal stage order is preserved;
- interruption tasks stop before their final patch stage;
- the focus task final stage is the final turn;
- exactly one turn is scored.

A focus-control case contains only the same focus task stages in order, with the
same final patch scoring interface.

## 5. Release Invariants

The public release verifier checks:

- 500 tasks;
- 500 switched cases;
- 500 matched controls;
- 500 unique focus tasks;
- exactly one scored final focus turn per case;
- the scored turn is the final turn;
- no forbidden public fields such as source URLs, reference patches, test
  patches, target files, or implementation-file lists.

Run:

```bash
python3 scripts/verify_release.py --data-dir data --expected-count 500
```

## 6. Public/Private Boundary

The public v1 repository is suitable for reproducing the prompt stream, the
controller/answer-agent protocol, and demo-format scoring. Full leaderboard
scoring requires private held-out evaluation material.

This boundary is deliberate: the benchmark can be inspected and integrated
publicly without exposing hidden tests or reference solutions.
