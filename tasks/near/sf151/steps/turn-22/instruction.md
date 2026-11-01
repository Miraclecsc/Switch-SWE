One more thing: I'd expect test_asyncio_exception_handler to pass, then fail in teardown:

Handler restoration also applies when the supplied callable fails synchronously before returning an awaitable. A following successful call must return its own value without replaying earlier callback or callable errors.