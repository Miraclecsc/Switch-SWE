One more thing: Looks like if the future is cancelled result is not bound maybe?

Preserve exception propagation and cancellation cleanup while adding the explicit Context option. Later ordinary worker calls must see their own caller's bindings rather than a previous explicit Context. Context snapshot objects are private to each call; do not retain them in global or per-worker caches.
Implement and validate this.