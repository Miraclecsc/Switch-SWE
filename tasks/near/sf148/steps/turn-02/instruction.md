For the checkout at /work/w00, Added context manager mix-in classes

<!-- Thank you for your contribution! -->
## Changes

This adds two new mix-in classes: `ContextManagerMixin` and `AsyncContextManagerMixin`. They're meant to enable users to write context manager classes in the same way as `@contextmanager` and `@asynccontextmanager`, respectively. The aim is to enable users to more easily embed cancel scopes and task groups into other context manager classes.

## Checklist

If this is a user-facing code change, like a bugfix or a new feature, please ensure that
you've fulfilled the following conditions (where applicable):

- [X] You've added tests (in `tests/`) added which would fail without your patch
- [X] You've updated the documentation (in `docs/`, in case of behavior changes or new
features)
- [X] You've added a new changelog entry (in `docs/versionhistory.rst`).

If this is a trivial change, like a typo fix or a code reformatting, then you can ignore
these instructions.

### Updating the changelog

If there are no entries after the last release, use `**UNRELEASED**` as the version.
If, say, your patch fixes issue <span>#</span>123, the entry should look like this:

```
- Fix big bad boo-boo in task groups
  (`#123 <https://github.com/agronholm/anyio/issues/123>`_; PR by @yourgithubaccount)
```

If there's no issue linked, just link to your pull request instead by updating the
changelog after you've created the PR.

Open issues: - ~Can't type annotate to return `Self`~ - ~Should `T` be co/contravariant?~ (typeshed uses a covariant typevar in `AbstractAsyncContextManager`) - ~This may require a new documentation section~ - ~We should probably check for corner cases in the `@asynccontextmanager` implementation~ - ~Reentrancy (must consider the case where the CM is entered twice before exiting)~ (disallowed re-entrancy)