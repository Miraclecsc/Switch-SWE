# Clean Evaluation Protocol (CEP)

The Clean Evaluation Protocol defines what the evaluated agent can see and what
the trusted controller must keep private.

## Roles

### Controller

The controller is trusted infrastructure. It:

1. loads the selected case;
2. creates a fresh workspace;
3. clones each required repository at the case-specified base commit;
4. removes `.git` from the answer-agent copy by default;
5. sends one prompt turn at a time;
6. records outputs;
7. extracts the final focus-task patch;
8. invokes a scorer if one is configured;
9. deletes the workspace unless debugging is requested.

### Answer Agent

The answer agent is the evaluated coding system. It receives:

- the prepared workspace;
- the current turn prompt;
- normal shell/file access inside that workspace.

It must not receive:

- the full case JSON;
- future turns;
- reference patches;
- hidden tests;
- target files;
- scorer metadata;
- upstream PR/commit/review URLs.

## Workspace Policy

- A case gets a fresh workspace.
- Repositories are checked out at their base commits.
- `.git` is removed from the answer-agent repository copies by default.
- Workspace state persists across turns within a case.
- Workspaces reset between cases.
- The controller may keep private base snapshots outside the answer-agent
  workspace for diff collection and scoring.

## Prompt Delivery

Turns are sent in `turn_sequence`. The answer agent receives only the current
`prompt_text`. If an agent CLI is stateless by default, the adapter should use
that tool's session or resume mechanism so that the answer agent, not the
controller, carries the within-case memory.

## Final Patch

Only the final focus-task turn is scored. The final response should be strict
JSON with keys:

```json
{
  "task_id": "...",
  "subtask_id": "...",
  "analysis": "...",
  "files": [],
  "patch": "diff --git ..."
}
```

The `patch` field must be a standalone unified diff for the focus repository.
Patches for interruption tasks must not be included.

## Scoring Modes

### Demo Scoring

The public repository includes `examples/demo_scorer/demo_score_patch.py`. It
checks only that the submitted patch is a non-empty unified diff. This is for
integration testing and does not establish benchmark accuracy.

### Leaderboard Scoring

Leaderboard scoring is executable patch evaluation. The scorer starts from a
clean checkout of the focus repository at the base commit, applies the submitted
patch, enables held-out tests, and marks the case correct if the patched
checkout passes those tests.

The public repository does not include held-out tests or the private scorer.
