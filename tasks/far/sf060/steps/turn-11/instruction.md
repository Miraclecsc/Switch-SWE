Please check this too: Does `winloop` have releases that lack `shutdown_default_executor()`?

Expose the same loop_factory_fallbacks keyword on the asyncio that type, with identical factory selection and fallback behavior. Validate the whole fallback sequence as callables before opening a loop; invalid entries raise TypeError. Explicit loop_factory still overrides use_uvloop, while the optional provider selected by use_uvloop can itself use these allocation fallbacks.
Implement and validate this.