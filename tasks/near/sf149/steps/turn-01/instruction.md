I have this in /work/w01: Fix the older asynchronous memory object stream in src/anyio/streams/memory.py.
Keep receive_nowait() and send_nowait() awaitable.

When a receive frees space, the oldest blocked sender must be admitted and
unblocked by that first receive, including when the buffer was already nonempty.
Store its item before notifying it, and return buffered items in FIFO order.
For example, a capacity-one stream containing 'hello' with a blocked send('anyio')
must unblock that sender after one receive_nowait() returns 'hello'; the next
receive_nowait() returns 'anyio'. Preserve closed-handle, EOF, clone, and
ordinary send/receive behavior. Use a bounded task-group regression test.
Later turns will add requirements to this stream implementation.