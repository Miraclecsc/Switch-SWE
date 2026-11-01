For the checkout at /work/w04, Add auto-detection of self-implemented methods

This adds the feature to auto-detect existing methods so the creation doesn't have to be prevented by hand. This has been confusing our users for a while (see #324, #416).  It should become `True` by default when the new APIs emerge (attr.auto/attrs.define – this is actually one of the last blockers for me to start working on them).

Typing requires an update to the mypy plugin to work correctly (currently it says `tests/typing_example.py:193: error: Name '__init__' already defined on line 190`).

There is really only one controversial open question: if a method is detected, should it just prevent the one method or all of the related ones? E.g. if I define `__eq__`, what about `__ne__`?

I have decided to take the presence of _any_ method that belongs to a flag to set the flag to False because it's easier to reason about. I'm open to discussion tho.

Add auto-detection of self-implemented methods This adds the feature to auto-detect existing methods so the creation doesn't have to be prevented by hand. This has been confusing our users for a while (see #324, #416). It should become `True` by default when the new APIs emerge (attr.auto/attrs.define – this is actually one of the last blockers for me to start working on them). Typing requires an update to the mypy plugin to work correctly (currently it says `tests/typing_example.py:193: error: Name '__init__' already defined on line 190`). There is really only one controversial open question: if a method is detected, should it just prevent the one method or all of the related ones? E.g. if I define `__eq__`, what about `__ne__`? I have decided to take the presence of _any_ method that belongs to a flag to set the flag to False because it's easier to reason about. I'm open to discussion tho.

Is the concept with `__init__` that it replaces the auto-created init, or that it gets turned into `post_attr_init_`?