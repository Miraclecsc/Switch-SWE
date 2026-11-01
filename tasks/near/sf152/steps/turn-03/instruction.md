There's something to adjust in /work/w00: Added an exception handler in the asyncio test runner

It will now raise all the capture exceptions if the test function completes without raising any exceptions of its own.

Closes #205.

Added an exception handler in the asyncio test runner It will now raise all the capture exceptions if the test function completes without raising any exceptions of its own. Closes #205.

BaseExceptions crash the event loop; the handler is never called with such an exception.