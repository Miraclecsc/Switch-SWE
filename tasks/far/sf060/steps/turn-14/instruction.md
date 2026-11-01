One more thing: your PR also fixes a problem where func and args are kept alive, can you add a test for this also?

The supplied Context is caller-owned: take an independent shallow Context snapshot before waiting for the thread limiter. Worker assignments must not mutate either that Context or the calling task's Context. Reusing the same supplied Context concurrently must work. A worker still has no active async-library marker, and its normal from_thread integration must remain available.
Implement and validate this.