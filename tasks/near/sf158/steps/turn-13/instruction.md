Also, Test failed with `RuntimeError` being raised from `raise_exc`

With raise_app_exceptions=False, a normally returned incomplete response must be recoverable just like an exception: preserve a sent status, all headers including duplicates, and partial body bytes; if no response started use status 500 and empty headers/body. Complete the response so reading it cannot hang.