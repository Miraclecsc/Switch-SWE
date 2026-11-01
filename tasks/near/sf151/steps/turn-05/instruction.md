In the checkout at /work/w00, Made start_blocking_portal() a context manager

* Ensures that the thread is joined when exiting
* Eliminates a potentially confusing regular context manager from BlockingPortal

Made start_blocking_portal() a context manager * Ensures that the thread is joined when exiting * Eliminates a potentially confusing regular context manager from BlockingPortal

calling `start_blocking_portal(backend="twisted")` hangs forever