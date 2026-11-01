Please check this too: Also added bytes supports for the other methods and added tests for each distinct one. I had to duplicate a bit of logic from Pathlib around stat()ing.

Hm, wouldn't `PathLike[Any]` work here, given that the variable is bound to `str` and `bytes` anyway?