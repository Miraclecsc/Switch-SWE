There's something to adjust in /work/w02: Accept bytes for Unix socket paths.

*nix paths are an arbitrary sequence of bytes.

While this is *almost* an annotations only patch, it does replace the use of `str()`. Perhaps there should be a test that creates a socket from a bytes-based path that doesn't cleanly translate to ASCII?

It would test that a bytes-based socket path would not result in `UnicodeDecodeError`, as it could without this patch.