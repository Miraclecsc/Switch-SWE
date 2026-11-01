And here, How about a `pilot.double_click` and `pilot.triple_click` (in addition to the `times` parameter?

Make Pilot.click(times=N) emit all N mouse-down/up/click sequences without leaking Click-only chain arguments into other event types. double_click and triple_click must return the same boolean targeting result as click. Preserve original click aliases and raw event tests.