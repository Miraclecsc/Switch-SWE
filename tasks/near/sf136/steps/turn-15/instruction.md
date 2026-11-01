Please check this too: > I will fix this, then it's ready to merge. I just did that, and rebased on top of `main`.

Complete err=True routing on the Windows split-prompt path too: the final character written by the input callback must go to stderr with the prefix, for prompt and confirm including empty suffixes. Restore stdout after normal return and after input exceptions.