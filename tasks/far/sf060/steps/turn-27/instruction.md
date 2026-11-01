Please check this too: Somewhat off topic: If we are getting into `functools.reduce`/`itertools`, Consider that we should add `anyio.as_safe_stream` (a port of `trio.as_safe_channel`).

the off-topic safe-stream idea remains outside scope. Instead implement cache_clear as a generation boundary: clear completed entries and reset statistics immediately; a computation already in progress may still return to its original caller, but its result must not repopulate the cleared cache or overwrite a value computed after clear. New callers use the new generation.
Implement and validate this.