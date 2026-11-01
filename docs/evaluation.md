# Evaluation protocol

Switch-SWE measures final focus-task resolution after a conversation moves among
multiple unfinished coding tasks. This repository provides the frozen inputs and
initial-source preparation tools. Full historical grading additionally requires
the separately maintained private verifier and qualified runtime assets.

## Session execution

1. Choose a complete pair from `data/pairs.json` and fix the model, adapter,
   context policy, tool permissions and budget before executing either arm.
2. Prepare fresh checkouts from each case's pinned commits **and** its initial
   overlays. A baseline has one checkout; a switched session has five.
3. Start a fresh native agent conversation for the arm. Keep both its history
   and checkout state across turns. Never carry state between arms or pairs.
4. Send the `prompt` text of one turn at a time, in its frozen order. Mount the
   prepared directories at `/work/w00`, `/work/w01`, etc. in the agent's sandbox.
   Do not supply future turns, role labels, a focus flag, split metadata, the
   whole benchmark repository or the private grader.
5. Record responses and tool activity. Treat the final `A_final` answer as the
   submission. The frozen protocol requests strict JSON with `task_id`,
   `analysis`, and a complete unified `patch`.
6. Apply the submitted focus patch to the original base in a separate verifier
   environment. Count resolution only when the required failing-to-passing and
   passing-to-passing tests are collected and pass.

The historical protocol scores the **patch in the final answer**. Extracting
the disk diff, accepting malformed JSON, or repairing an answer changes the
evaluation contract. Such variants can be useful, but must have a distinct
reported protocol. Some historical model reports used packaging normalization;
their results should not be silently pooled with strict parsing.

The published case-level `task_id` and the opaque answer ID in the final prompt
serve different purposes. Validate the answer ID against the actual final
prompt. Do not replace it with controller metadata.

## Resources and failures

The archived execution policy uses a 900-second limit per CLI invocation and
allows up to three timeout continuations per case. This is not a 900-second
total budget for an entire session. A single request can span multiple
900-second invocations; the three timeout continuations are shared across the
case. Completed turns are not resent on resume.
Most frozen environments use 2 vCPU / 8 GiB; the two arms of `sf047` and `sf048`
use 8 vCPU / 16 GiB. These are historical profiles, not guarantees that all
public preparations run on any machine with those resources.

Report graded outcomes, exhausted timeouts, provider failures, setup failures
and missing results separately. A setup failure is not a demonstrated wrong
solution. Preserve attempts and continuation lineage rather than retrying until
a preferred outcome appears.

## Metrics

For a declared set `P` of compatible pairs with both arms graded:

```text
baseline_rate = mean(resolved_baseline[i] for i in P)
switched_rate = mean(resolved_switched[i] for i in P)
paired_gap_pp = 100 × (baseline_rate - switched_rate)
```

Report `|P|`, missing/ungraded arms, and both directions of outcome flips.
Report near and far separately with their actual denominators. Their gap
difference is a comparison between two different groups of tasks; it is not
a within-task near-versus-far intervention.

An all-target verified-resolution rate can instead use 200 targets, or 100 per
split, with unverified success contributing zero. Label that definition
explicitly; it differs from a graded-only resolution rate.

Token, tool-call and inference-step metrics should identify whether they cover
the entire switched conversation or selected focus turns, and whether auxiliary
context-manager calls are included. The historical resource tables define
**Focus** as nonfinal focus requests after the first focus request, including
their same-session continuations. This excludes interruptions and finalization;
it does not require an interruption immediately before each included request.
Report the number of records with usable telemetry for each metric.

## Historical results

The local September 25 audit found different numbers of complete graded pairs
across model campaigns. Older campaigns may also combine prompt revisions or
adapter contracts. This public packaging therefore does not promote draft
tables into a full-200 leaderboard.

The September 16 prompt clarification did not recompute prior results. Results
must be bound to their original prompts, model, adapter, context policy,
runtime, scorer and budgets. Dataset availability, archived environment
qualification and completion of model evaluation are separate facts.

See the [data card](data-card.md) for concrete deviations from perfect matching.
Claims of a pure causal switching effect require taking those deviations and
development-time selection into account.
