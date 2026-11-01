# Dataset maintenance

Tasks use Harbor's native multi-step format. Each instruction is an unchanged
request from the frozen switched cohort; the final step grades the focus
checkout through Harbor's separate verifier.

```sh
# Validate all published tasks with the pinned Harbor installation.
python tools/check_tasks.py

# Re-export from the original prepared assets.
python tools/export_tasks.py \
  --source /path/to/releases/fixed200-v1 \
  --output /path/to/new-tasks

# Grader tests use pytest inside their temporary fixture repositories.
uv pip install pytest
python -m unittest discover -s tools -p test_verifier.py
```

The exporter reads the original cohort, source overlays, dependency metadata
and grading contracts. It emits only the 200 switched sessions. Python and
package versions are rebuilt from public images and packages; Pandas tasks
recompile extensions before grading.

Harbor supplies step execution, native session resume, artifacts, containers
and rewards. Steps have a 900-second agent budget; only the final step's
reward counts. Its verifier compares the final focus checkout with the
original base, applies the test patch, and checks every required F2P/P2P result.
Run reference solutions with `harbor run -p <task> -a oracle`.

Checked on November 1, 2026: upstream Harbor loaded all 200 tasks and all 4,513
prompt files matched the frozen source. The grader's 15 tests passed; real
`sf076` (far) and `sf117` (near) each scored 0 for the empty patch and 1 for the
reference. Docker builds and full container runs remain to be checked on a
Docker host.
