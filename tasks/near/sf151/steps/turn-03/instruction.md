Please check this too: BaseExceptions crash the event loop; the handler is never called with such an exception.

The asyncio TestRunner.call operation must preserve any exception handler already installed on its loop and restore that exact handler after success or failure. Capture ordinary Exception instances from callbacks for the current call; do not retain them for later calls.