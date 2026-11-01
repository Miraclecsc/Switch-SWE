Also, you'll need to run a `gc.collect()` here to get this passing on pypy

Extend the same worker-context ownership task with keyword-only context=None on anyio.to_thread.run_sync. When a contextvars.Context is supplied, execute that work item with its bindings; None keeps the existing caller-context behavior. Preserve args, limiter, return values, exceptions and the existing cancellation options. This is part of the original thread context work, not a new executor API.
Implement and validate this.