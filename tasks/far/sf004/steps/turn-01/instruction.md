I have this in /work/w01: Fix the asyncio bug where a cancellation raised by
`anyio.from_thread.check_cancelled()` escapes the applicable cancel scope.
The original test suite and Trio behavior must continue to work. A minimal
behavior to support is:

```python
def worker():
    from_thread.run_sync(scope.cancel)
    from_thread.check_cancelled()

with CancelScope() as scope:
    await to_thread.run_sync(worker)

assert scope.cancelled_caught
```

Provide a suitable regression. There is no restriction on implementing a complete
solution now.