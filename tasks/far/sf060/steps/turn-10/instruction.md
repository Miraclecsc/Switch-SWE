One more thing: @agronholm I'm fixing the issue. one moment I added winloop to pyproject.toml I just forgot to register it. As for the flag I'm reverting that idea.

Extend this loop-selection API with backend_options['loop_factory_fallbacks'], a finite sequence of zero-argument loop factories. If creation by the selected primary factory raises OSError, try these factories in order and return the first successfully created loop. An empty sequence preserves existing behavior. This is a loop-allocation fallback, not a retry of the user's coroutine.
Implement and validate this.