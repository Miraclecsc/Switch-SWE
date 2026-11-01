One more thing: Extend the same memory object send stream with a new coroutine:
    await send.send_and_wait(item)

This supports producers that need confirmation of consumer receipt, beyond
buffer admission. It returns None only after a receiver has consumed this exact
item through receive(), that method, or iteration. A successful ordinary
send() or that method must still complete at buffer admission as before.

send_and_wait must work with zero and positive capacities, with an already
waiting receiver, with blocked senders, and through stream clones. It must share
FIFO ordering with ordinary items and return the original payload object to the
receiver, never a receipt wrapper. Freeing one slot can admit the next sender,
but admission must not acknowledge that next item until it too is consumed.
Keep the first-turn fix and all existing tests. Add behavior tests.