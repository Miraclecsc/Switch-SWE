Also, This PR doesn't include changes to `BlockingPortal`. Perhaps it should?

Extend TaskHandle with add_done_callback(callback). Synchronous callbacks receive the completed handle and run exactly once per registration after success, failure or cancellation, when public status/result properties already reflect completion. Registering on an already completed handle invokes it immediately.