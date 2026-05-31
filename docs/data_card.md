# Data Card

## Dataset Name

SessionSwitchBench v1.

## Purpose

SessionSwitchBench v1 evaluates coding agents under within-session task
switching. It is designed to complement isolated repository repair benchmarks by
testing whether an agent can maintain and resume a focus repair task while
handling interleaved interruption tasks in the same session.

## Public Release Contents

| Artifact | Count |
| --- | ---: |
| Public tasks | 500 |
| Switched cases | 500 |
| Matched focus-control cases | 500 |
| Unique focus tasks | 500 |
| Repositories | 410 |

## Case Statistics

| Statistic | Value |
| --- | ---: |
| Mean turns per switched case | 14.494 |
| Median turns per switched case | 14 |
| Turn range | 9--20 |
| Mean unique tasks per switched case | 7.034 |
| Median unique tasks per switched case | 7 |
| Unique task range | 5--9 |
| Mean interruption tasks per switched case | 6.034 |
| Median interruption tasks per switched case | 6 |
| Interruption task range | 4--8 |
| Mean focus stages | 4.602 |
| Median focus stages | 5 |
| Focus stage range | 3--6 |

## Stage Distribution

| Stages per task | Tasks |
| ---: | ---: |
| 3 | 9 |
| 4 | 211 |
| 5 | 250 |
| 6 | 30 |

## Source Lineage

The 500 tasks are derived from SWE-bench-family repository repair tasks that
passed internal strict executable validation. The public release anonymizes task
ids and omits source labels, reference patches, test patches, and original
instance ids.

Private construction metadata records the following source-label distribution:

| Source label | Tasks |
| --- | ---: |
| `SWE-bench-extra` | 372 |
| `SWE-bench_Verified` | 52 |
| `SWE-bench-dev` | 43 |
| `SWE-bench-Live` | 21 |
| `SWE-bench_Lite` | 6 |
| `SWE-bench` | 6 |

## Intended Use

- Evaluating coding agents with a controller/answer-agent protocol.
- Comparing switched cases against matched focus-control cases.
- Studying within-session memory, context management, and task isolation.
- Developing agent adapters for clean multi-turn coding evaluation.

## Not Intended For

- Training on hidden evaluation targets.
- Claiming official SWE-bench leaderboard performance.
- Treating the public demo scorer as executable benchmark scoring.
- Exposing private metadata or scorer artifacts to evaluated agents.

## Limitations

- The public repository includes a demo scorer only.
- Full leaderboard scoring requires private held-out tests.
- v1 stages are workflow decompositions of selected repair tasks, not naturally
  collected multi-event task histories.
- v1 should be described as SWE-bench-family-derived, not as an official
  SWE-bench split.
