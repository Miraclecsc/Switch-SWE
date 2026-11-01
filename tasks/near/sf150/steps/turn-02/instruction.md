For the checkout at /work/w03, Added backwards compatibility code and migration docs

These changes will be backported to the 2.x branch. They allow library authors to write code compatible with both major releases.

Looks OK. Now if there was a semantic patching tool for Python I could use to autoreplace all the calls that actually refer to anyio objects (and *only* those) I'd be even more happy. :-/