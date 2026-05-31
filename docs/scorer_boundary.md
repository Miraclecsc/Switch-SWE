# Scorer Boundary

This repository intentionally separates public protocol code from private
leaderboard scoring material.

## Public Demo Scorer

`examples/demo_scorer/demo_score_patch.py` checks whether a submitted patch is a
non-empty unified diff. It is useful for verifying that an agent adapter and the
controller can exchange a machine-readable final patch.

The demo scorer does not:

- clone repositories;
- install dependencies;
- apply patches;
- run tests;
- inspect reference patches;
- decide whether a repair is semantically correct.

## Private Leaderboard Scorer

Full scoring is executable patch evaluation. It requires held-out evaluation
material and environment recipes that are not included in the public v1 repo.

For each submitted case, the private scorer:

1. resolves the focus task;
2. checks out the focus repository at its base commit;
3. applies the submitted patch;
4. enables held-out tests;
5. runs the focused test command in an isolated environment;
6. reports whether the patch passes.

Submitted patches are judged by behavior under tests, not by textual equality to
the reference patch.

## Why Keep This Boundary?

Publishing hidden tests, reference patches, or target-file metadata would make
the benchmark easier to game and would contaminate agent-facing inputs. The
public repo therefore exposes the evaluation protocol and demo integration path,
while private leaderboard runs keep the executable oracle separate.
