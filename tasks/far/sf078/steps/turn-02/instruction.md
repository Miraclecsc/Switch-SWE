For the checkout at /work/w01, Fix debug wheel support for Python 3.8

Python 3.8 debug builds can load both debug and non-debug wheels, so support both.

Also made debug build detection on Windows more robust.

Closes #172 and #194

I don't think it really does since it means you have to use `abis.insert(0, ...)` to keep the non-conditional case accurate, but since I need this release to go out for something at work I'm going to make the change to help get this PR merged.