And here, IIRC we still need to do to cover `asyncio.coroutine`-based coros.

Preserve the original marked generator-coroutine protocol for cache dispatch where that protocol is supported: cache its awaited result, not an exhausted generator object. Also handle waiters across failure and cache_clear: they must retry against the current cache generation, without leaking a pending entry or deadlocking. Use deterministic event-based tests.
Implement and validate this.