Also, Looks like `coverage` checks are failing because this bug was ensuring code got covered. I will adjust now

Add optional keyword-only keepends=False to Response.iter_lines and Response.aiter_lines. With True, retain original line separators exactly, matching str.splitlines(keepends=True) for the fully decoded text while still consuming the body incrementally. Default behavior is unchanged.