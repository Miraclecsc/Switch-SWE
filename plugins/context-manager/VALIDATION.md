# Validation of the standalone v003 distribution

Fresh verification on 2026-11-01 used Node **24.21.0**, Python **3.12.3**, and
the original OpenCode **1.18.2** executable. Its SHA-256 was checked before each
integration run:
`14d26f3eee4a0770e8a5c27103bee0998f79a91c052eb6629cd7f0e8bcdae1b9`.

| Check | Result |
| --- | --- |
| Original `node --test test/*.test.mjs` | 16 passed, 0 failed |
| Standalone wrapper `python3 -B test/wrapper_test.py` | 4 passed |
| Native integration, `a` | Passed; 3 main requests, 3 routing requests, 0 memory requests |
| Native integration, `x` | Passed; 3 main requests, 3 routing requests, 2 memory requests |
| Native integration, `off` | Passed; 3 main requests, 0 auxiliary requests |

All three native tests retained the same native session over three CLI
invocations and checked the exported history. A/X removed the distractor topic
from the final outgoing provider context while keeping it in native history.
X inserted a historical memory in the outgoing request only. Off retained the
distractor topic and made no auxiliary calls. All provider calls went to the
test's local simulated endpoint, with dummy credentials; no real model API was
called.

Local raw integration evidence:

- `/data/context-integration-a-pj1_nb9k/result.json`
- `/data/context-integration-x-9k5k5c6r/result.json`
- `/data/context-integration-off-ynhb_na9/result.json`

Those directories also contain request captures, native exports, isolated
runtime state, and stdout/stderr. They are verification scratch, not part of
this package; rerunning the tests creates fresh evidence.

The original 16 tests cover topic return, current-turn/tool preservation,
uncertain and failed routing, session isolation, restart deduplication, bounded
memory preparation, failed-memory guards, original user-instruction retention,
oversized-memory fallback, provider request construction, array identity, and
compaction passthrough. The new wrapper tests cover default X, A, off, invalid
mode rejection, argument forwarding, and preservation of existing configuration.

The four runtime files and original JavaScript tests match the selected frozen
v003 snapshot and the full-evaluation snapshot byte for byte. The integration
test was adapted to validate the executable pin, place scratch outside the
package, and cover off mode. No runtime behavior was changed. The manifest
contains no dependency or install script, and the npm package file list is
explicitly limited to source, tests, provenance, license, and documentation.

All delivered text was reviewed and scanned for private-key blocks, common
provider/token formats, credential-bearing URLs, and literal credential
assignments. No real credentials were found. `FAKE_LOCAL_KEY` and `local-secret`
are loopback test fixtures; `{env:PROVIDER_API_KEY}` is a documentation
placeholder. No secret file, auth store, runtime directory, binary, benchmark
conversation, or operator script was copied. This is a bounded check of these
delivered files, not a scan or certification of the original workspace.

Compatibility with other OpenCode releases, real-model semantic routing and
memory quality, production proxy behavior, simultaneous processes sharing
session state, and final 100 near + 100 far benchmark performance were not
validated. No benchmark outcome is claimed by this packaging work.
