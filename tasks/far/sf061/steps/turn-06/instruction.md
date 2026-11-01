I have this in /work/w00: Always rewind files on multipart uploads.

Raised in #2064

- [x] Failing test case.
- [x] Implement rewind fix.

Always rewind files on multipart uploads. Raised in #2064 - [x] Failing test case. - [x] Implement rewind fix.

Waiting on a release of `httpcore` with in order to fix the test suite. Once we've got that I'll re-run the suite to demo that the test currently fails, and then push the fix. **Edit** Okay, done. Test suite prior to the fix [fails with this](

This is more of a question, so we do `seek` for the first file upload too, right?