# OpenCode context manager v003

This is the user's selected **v003** plugin for **OpenCode 1.18.2**. The runtime
files `plugin.mjs`, `manager.mjs`, `analyzer.mjs`, and `opencode_plus` are copied
unchanged from the measured development snapshot and match the subsequent full
evaluation snapshot. `0.0.0-v003` is this distribution's package label, not a new
plugin implementation or an npm release.

## Run

Use an existing OpenCode **1.18.2** executable and Python 3. The plugin has no npm
dependencies and requires no build. Node 24 is used for the standalone tests;
OpenCode runs the plugin using its own runtime.

```sh
cd plugins/context-manager
OPENCODE_UPSTREAM_BIN=/absolute/path/to/opencode ./opencode_plus run "Your request"
OPENCODE_CONTEXT_MODE=a OPENCODE_UPSTREAM_BIN=/absolute/path/to/opencode ./opencode_plus run "Your request"
OPENCODE_CONTEXT_MODE=off OPENCODE_UPSTREAM_BIN=/absolute/path/to/opencode ./opencode_plus run "Your request"
```

The default mode is `x`. Other CLI arguments, including `--session`, pass through
unchanged. The wrapper appends the local plugin to `OPENCODE_CONFIG_CONTENT` for
its child process. It does not write your OpenCode configuration. An explicit
`OPENCODE_UPSTREAM_BIN` must be an executable path, not just a command name.

You can copy this whole directory elsewhere and use the wrapper there.
Alternatively, add the following entry to your existing OpenCode configuration,
substituting the absolute path:

```json
{
  "plugin": [
    ["file:///absolute/path/to/context-manager/plugin.mjs", {"mode": "x"}]
  ]
}
```

Use either direct registration or the wrapper to avoid loading the plugin twice.
Keep `manager.mjs` and `analyzer.mjs` beside `plugin.mjs`.

## Provider configuration

The auxiliary analyzer needs an OpenAI-compatible chat-completions provider with
explicit `provider.<providerID>.options.baseURL` and `apiKey` in the OpenCode
runtime configuration. The selected message's provider and model are used.
Credentials available only in OpenCode's separate auth store are not read by
this plugin. Configure a reference such as `"apiKey": "{env:PROVIDER_API_KEY}"`
and set that variable outside this package.

Only HTTPS endpoints and loopback HTTP endpoints are accepted. The analyzer
requests JSON responses with an 8,192-token output limit and a 120-second timeout
per request. Topic routing and memory generation make additional provider calls
and send relevant conversation content to that provider.

## Modes and storage

| Mode | Behavior |
| --- | --- |
| `off` | The wrapper does not add the plugin. A directly registered plugin in off mode leaves messages unchanged and makes no auxiliary calls. |
| `a` | Routes user turns to topics and selects original history relevant to the current topic, retaining unassigned history and shared instructions. |
| `x` | Adds evidence-linked topic memory, preserves selected original user instructions and recent exchanges, and replaces older exchanges only when the complete memory fits the injection budget. |

Projection affects the current provider request; native session history is
preserved. Compaction passes through all topics. Uncertain routing or analysis
failures retain original history. Failed memory preparation keeps its original
evidence and is not repeated for every tool step.

State defaults to
`$XDG_STATE_HOME/opencode-context-manager/<project-hash>/`, or
`~/.local/state/opencode-context-manager/<project-hash>/`. Set
`OPENCODE_CONTEXT_STATE_DIR` to an isolated directory when comparing modes.
State contains topic text and memory; usage, lifecycle, and audit files record
activity. New directories use mode `0700` and files use `0600`; existing
permissions are not repaired. No credentials or recorded conversations are
included in this distribution.

## Test

The existing JavaScript tests use Node's built-in test runner. Wrapper tests use
Python's standard library. No dependency installation is needed.

```sh
node --test test/*.test.mjs
python3 -B test/wrapper_test.py
# Equivalent when npm is available:
npm test
```

The integration test requires Python 3.11 or newer and uses the actual pinned OpenCode executable and a local
HTTP provider with dummy credentials. It checks outgoing context, restored
topics, memory injection, and unchanged exported native history.

```sh
export OPENCODE_TEST_BINARY=/absolute/path/to/opencode
python3 -B test/integration.py --mode a
python3 -B test/integration.py --mode x
python3 -B test/integration.py --mode off
```

The test requires the historical executable SHA-256
`14d26f3eee4a0770e8a5c27103bee0998f79a91c052eb6629cd7f0e8bcdae1b9`.
It uses a fresh temporary home and workspace, disables model catalog downloads,
default plugins, and automatic updates, and sets npm's offline mode. Evidence
stays in a temporary directory printed on completion; `--output-dir` selects
its parent. No real model API is called. The binary is not bundled.

## Provenance and limits

Source repository:
`/mnt/jfs/mengziyang/changshuochen/SessionSwitchBench/workspaces/opencode-1.18.2-dev-20260920`

Delivery commit: `07304054b8bfcb535611791c064d4169de005bcf`.
The original documented upstream baseline is
`70b56a0a93d366889cae950379cc9d2537148fa2` (OpenCode 1.18.2).
The chosen snapshot is `context-manager/.runs/v003/module`; the matching full
evaluation snapshot is `context-manager/.runs/full-v003-mp48/module`.
`PROVENANCE.json` records individual hashes and the version-selection evidence.
The source repository's MIT license is retained.

The historical user explicitly selected v003 after comparing development
versions. v004's experimental memory retry is not included. The working tree's
later operator changes, experimental campaign scripts, raw results, credentials,
and the binary are excluded.

Compatibility is verified only against the pinned OpenCode 1.18.2 executable.
The experimental hook contract may differ in other versions. The unchanged
wrapper does not itself enforce the executable pin; the integration test does.
Node 24.21.0 is the tested standalone JavaScript runtime.

Routing accuracy and memory quality depend on the auxiliary model. Evidence is
bounded and may be truncated. A JSON response format unsupported by the provider
can cause fallback. v003 has no invalid-memory regeneration retry. It serializes
one session inside a manager instance but provides no cross-process state lock;
avoid concurrent CLI processes writing the same session state. Local simulated
provider tests do not establish real-model quality, production proxy behavior,
or an improvement on the final 100 near + 100 far benchmark.
