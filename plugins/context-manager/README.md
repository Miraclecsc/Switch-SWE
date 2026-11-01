# OpenCode context manager

**RCM v003**, tested with **OpenCode 1.18.2**. It routes conversation history by task and maintains memory for returning to unfinished work.

## Run

Requires an OpenCode 1.18.2 executable and Python 3. No build or npm install is needed.

```sh
OPENCODE_UPSTREAM_BIN=/absolute/path/to/opencode \
  ./opencode_plus run "Your coding request"
```

Run this from the plugin directory, or use the wrapper's full path. Other OpenCode arguments, including `--session`, pass through. The wrapper adds the plugin to the child process's configuration.

| `OPENCODE_CONTEXT_MODE` | Behavior |
| --- | --- |
| `off` | Native OpenCode context |
| `a` | Task routing with relevant original history |
| `x` (default) | Task routing plus task-state memory |

```sh
OPENCODE_CONTEXT_MODE=a OPENCODE_UPSTREAM_BIN=/absolute/path/to/opencode \
  ./opencode_plus run "Continue the earlier task"
```

The native session keeps the complete history. RCM assembles the context sent with each model request.

## Provider setup

The analyzer uses the selected message's provider and model. Set an OpenAI-compatible chat-completions endpoint and API key through `provider.<providerID>.options.baseURL` and `apiKey` in your OpenCode configuration. Use an environment reference such as `"apiKey": "{env:PROVIDER_API_KEY}"`.

The endpoint must use HTTPS or loopback HTTP. The plugin reads these explicit configuration values; credentials stored only in OpenCode's separate auth store need to be configured here too. Routing and memory generation make additional model calls using conversation content.

## State

State is stored under `$XDG_STATE_HOME/opencode-context-manager/<project-hash>/`, or `~/.local/state/opencode-context-manager/<project-hash>/`. Set `OPENCODE_CONTEXT_STATE_DIR` to use another directory. Use separate state directories for independent evaluations or concurrent CLI processes.

## Tests

Standalone tests use Node 24 and Python 3:

```sh
node --test test/*.test.mjs
python3 -B test/wrapper_test.py
```

Integration tests use Python 3.11+, the pinned OpenCode executable and a local simulated provider:

```sh
export OPENCODE_TEST_BINARY=/absolute/path/to/opencode
python3 -B test/integration.py --mode a
python3 -B test/integration.py --mode x
python3 -B test/integration.py --mode off
```

[Validation results](VALIDATION.md) · [Source and version provenance](PROVENANCE.json) · [MIT license](LICENSE)
