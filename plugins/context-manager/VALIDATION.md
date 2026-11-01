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

These records contain request captures, native exports and runtime state.

The four runtime files and original JavaScript tests match the selected v003
development and full-evaluation snapshots. See [PROVENANCE.json](PROVENANCE.json)
for file hashes and source locations.
