I have this in /work/w01: gh-580: avoid calling await getaddrinfo(...) in exception handler
Preserve DNS failure identity and avoid attaching a failed literal-IP parse as its exception context.