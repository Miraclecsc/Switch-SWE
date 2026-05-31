# SessionSwitchBench

A benchmark for testing how coding agents handle task switching inside a single session.

Most repository-repair benchmarks give an agent one task at a time. SessionSwitchBench takes those repair tasks and interleaves a focus task with several unrelated interruption tasks in one continuous session. The agent has to keep working on the focus task across many turns while other tasks pull its attention away. Only the final focus-task patch is scored.

This is the v1 public release.

## What's in this repo

- 500 repository-repair tasks across 410 GitHub repositories
- 500 switched cases (a focus task interleaved with interruptions)
- 500 matched focus-control cases (the focus task alone, for comparison)
- A controller that runs cases against an agent and scores the result
- A release verifier and a demo scorer

The public data is prompt-clean. It does not contain reference patches, test patches, held-out tests, target files, upstream PR/commit URLs, or scorer internals. Full leaderboard scoring relies on held-out material that is not in this repo.

## Requirements

- Python 3.10+
- `git` (the controller clones repositories at their base commits)

No third-party Python packages are required to run the harness.

## Data

```text
data/tasks.json               # task definitions and workflow stages
data/session_cases.json       # switched cases (focus + interruptions)
data/focus_control_cases.json # matched controls
data/release_verification.json
```

Each switched case has:

- one focus task (turns labeled `A`)
- several interruption tasks, each with ordered stages
- a turn sequence such as `A1, G1, C1, A2, ... A_final`
- exactly one scored turn: the final focus turn

Task ids are anonymized (`ssb_v1_task_0001`, ...). Repository names and base commits are kept because the controller needs them to build the workspace.

## How evaluation works

The controller is trusted infrastructure; the agent is the system under test. For each case the controller:

1. clones every required repo at its base commit into a fresh workspace
2. removes `.git` from the agent's copy
3. sends one prompt at a time and records the output
4. collects the final focus-task patch and runs a scorer if one is configured

The agent only ever sees the current prompt and the prepared workspace, never the full case JSON or future turns. Workspace state persists within a case and resets between cases.

## Quick start

Verify the release:

```bash
python3 scripts/verify_release.py --data-dir data --expected-count 500
```

Expected output:

```json
{
  "status": "pass",
  "expected_count": 500,
  "tasks": 500,
  "session_cases": 500,
  "focus_control_cases": 500,
  "unique_focus_tasks": 500,
  "errors": []
}
```

Dry-run the controller (no cloning, just prints what each case would do):

```bash
python3 scripts/run_clean_agent_eval.py \
  --data-dir data \
  --max-cases 2 \
  --dry-run \
  --out-dir runs/dry
```

Run against the echo adapter, a smoke-test agent that does no real work:

```bash
python3 scripts/run_clean_agent_eval.py \
  --data-dir data \
  --max-cases 1 \
  --agent-command 'python3 $SSB_RELEASE_ROOT/examples/agent_adapters/echo_agent.py' \
  --out-dir runs/echo \
  --work-root runs/work
```

## Running a real agent

Replace `--agent-command` with a wrapper around your own agent (Codex, Claude Code, or anything that reads a prompt and edits files). The controller passes context through environment variables (`SSB_PROMPT_FILE`, `SSB_TURN_REPO_PATH`, `SSB_TURN_SCORED`, and others) and reads the final patch either from a JSON response on stdout or from the diff of the focus repo.

To score, pass `--score-command`. The included demo scorer only checks that the final patch is a non-empty unified diff:

```bash
python3 examples/demo_scorer/demo_score_patch.py \
  --submission runs/echo/cases/<case_id>/submission.json \
  --out runs/echo/demo_score.json
```

For real scoring, plug in your own scorer:

```bash
python3 scripts/run_clean_agent_eval.py \
  --data-dir data \
  --agent-command '<your-agent-wrapper>' \
  --score-command 'python3 <your-scorer> --submission $SSB_SUBMISSION_FILE --out $SSB_RESULT_DIR/score.json'
```

## Relationship to SWE-bench

SessionSwitchBench is derived from SWE-bench-family repository-repair tasks (see [swebench.com](https://www.swebench.com/) and [princeton-nlp/SWE-bench](https://github.com/princeton-nlp/SWE-bench)). Tasks that passed an internal strict-executable validation were each turned into a multi-stage workflow, then interleaved into session-switch cases.

This is not an official SWE-bench split or leaderboard. The change in what's being measured is the point: instead of solving one isolated issue, the agent has to maintain and resume several tasks within one session. Scoring stays patch-based and executable — the final focus patch is applied to a clean checkout and run against held-out tests.

## Documentation

- [Benchmark construction](docs/benchmark_construction.md)
- [Clean evaluation protocol](docs/clean_evaluation_protocol.md)
- [Data card](docs/data_card.md)
- [Scorer boundary](docs/scorer_boundary.md)

## License

MIT. See [LICENSE](LICENSE).

## Citation

Citation information will be added with the paper release.
