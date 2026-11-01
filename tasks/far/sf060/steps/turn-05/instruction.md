There's something to adjust in /work/w01: I specifically asked on Gitter to use `use_uvloop`. Why did you change your implementation?

Original task context for this directory: preserve the use_uvloop option, selecting uvloop off Windows and winloop on Windows in both anyio.run and the asyncio TestRunner. An explicit loop_factory wins. Preserve the original optional-dependency and platform-specific DNS/subprocess requirements. Make changes in this directory's checkout.
Implement and validate this.