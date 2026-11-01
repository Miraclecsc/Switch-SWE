And here, Sure. I already write two more tests about `function` and `args`, it does work. Howerer for the `result`, current solution fails. It seems to be the problem of asyncio itself.

Retain the original function, argument, context and result release fix. An explicit Context snapshot must remain alive while its work item is executing, but it must be releasable after completion when the application drops its references, without submitting another work item. Check independent concurrent uses of one Context.
Implement and validate this.