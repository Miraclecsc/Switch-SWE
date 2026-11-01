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
| Release identity tests | 4 tests passed on Python 3.10 and 3.12 |
| JavaScript plugin tests | 16 passed on Node 24.21.0 |
| Plugin wrapper tests | 4 passed |
| Native OpenCode integration | `a`, `x`, and `off` passed on the pinned 1.18.2 executable |
| Documentation | Internal links and Git whitespace checks passed |
| Upstream attribution | 46 license/attribution files from 19 repositories match recorded hashes |

The Python tests cover release identity, source reconstruction and independent
checkout state. The 400-case preparation check used dry-run plans.

The real `sf076_switched` preparation produced five packaging checkouts with
482 files and five initial file changes under Python 3.10.20. Each checkout had
one initial commit and a clean working tree.

Plugin integration used a local simulated provider to check routing, memory
injection and native session history. See the [plugin validation record](../plugins/context-manager/VALIDATION.md)
for the executable hash and request counts.
