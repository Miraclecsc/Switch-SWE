One more thing: Better yet, fix the test logic to check for the correct values

Only OSError from a loop factory permits fallback. Non-OSError factory exceptions and every exception from the user's coroutine propagate unchanged; never rerun the coroutine. If every factory fails with OSError, propagate the last exception object. Keep the original DNS platform rule: the Windows stdlib loop needs SOCK_STREAM whereas winloop must use the non-Windows resolver mode.
Implement and validate this.