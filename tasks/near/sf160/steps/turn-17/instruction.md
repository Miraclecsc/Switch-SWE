Also, This was the only way I could figure out how to cover an empty input to `LineDecoder.decode`.

Preserved separators include CRLF, standalone CR/LF, and the Unicode/control separators supported by str.splitlines. A CR at a chunk boundary must wait for the next nonempty decoded input so split CRLF stays together. Empty byte/text chunks must not create phantom lines.