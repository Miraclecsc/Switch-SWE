# Public package validation

Verification date: November 1, 2026.

| Check | Observed result |
| --- | --- |
| Dataset integrity | 200 pairs, 400 sessions, 100 near / 100 far, 19 repositories |
| Frozen effective case file | Matches `a47fefc8d3fc7251a25a56c74e5dd56637c7507cde1bcb085d921cf47d77da86` |
| Source overlays | All 200 source manifests match their cohort bindings |
| Initial source content | 856 blobs verified against their content hashes |
| Complete preparation plans | All 400 cases / 1,200 checkouts parsed and validated |
| Real source preparation | `sf076_switched`: five packaging checkouts, 482 files and five overlay writes verified |
| Python materializer and preparer | 37 tests passed on Python 3.10.20 and 3.12.3 |
| Release corruption checks | 4 tests passed on Python 3.10 and 3.12 |
| JavaScript plugin tests | 16 passed on Node 24.21.0 |
| Plugin wrapper tests | 4 passed |
| Native OpenCode integration | `a`, `x`, and `off` passed on the pinned 1.18.2 executable |
| Documentation | Internal links and Git whitespace checks passed |
| Upstream attribution | 46 license/attribution files from 19 repositories match recorded hashes |

The 41 Python tests include corrupt content, missing objects, unsafe paths,
independent checkout state, absence of successor Git objects, output reuse,
atomic publication, and attempted prompt/split/blob changes after rehashing a
manifest. Tests use temporary fixture repositories and no model service.

The 400-case preparation check is a dry-run metadata check. It does not mean
all 1,200 full source trees were materialized or their dependencies installed.

One real released case, `sf076_switched`, was additionally materialized on
JuiceFS from the existing `pypa/packaging` cache under Python 3.10.20. Each of
its five checkouts had exactly one commit, a clean working tree, no remotes or
alternates, and no unreachable Git objects. All 482 initial files matched their
declared source or overlay content and modes. The original bare cache was
unchanged. This check prepared source only; it did not install dependencies or
run task-grading tests.

Native plugin integration used a local simulated provider with dummy credentials.
It checked task projection, memory injection and preservation of the native
session. See the [plugin validation record](../plugins/context-manager/VALIDATION.md)
for the exact binary hash and request counts.

No real model evaluation was launched during this packaging task. These checks
establish package integrity and the tested tool behavior, not model performance
or a fresh qualification of the private evaluation environments.
