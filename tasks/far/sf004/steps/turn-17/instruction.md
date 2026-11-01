Also, Extend the asyncio backend's cancellation semantics . It uses existing public
APIs; no new public API is required. Apply the same rules on asyncio, uvloop and
asyncio's eager task factory. Keep the original backend compatibility tests,
including their Trio cases, passing.

**R1 — Preserve original behavior.** A worker's cancellation must still reach the
appropriate cancel scope, rather than leak or become an ordinary exception.
Retain the original 2 F2P and 142 P2P requirements without deletion, weakening,
renaming, skipping or replacing them.

**R2 — Associate cancellation with its scope.** A cancelled scope must not consume
a cancellation belonging to an unrelated scope merely because both are cancelled
or their error messages look alike. This includes a sibling operation's worker
result, a retained exception from an already-exited scope, and a parent's
cancellation raised inside a separately cancelled shielded child. In that last
case, the child must let it pass to the parent. A plain
`asyncio.CancelledError` with a message resembling AnyIO's cancellation message,
but without a genuine AnyIO cancellation in its context chain, remains external.
Preserve external exceptions and leave the unrelated scope's `cancelled_caught`
false. No exact message spelling, private representation, or object layout is
required.

**R3 — Preserve legitimate ancestor handoff.** Keep AnyIO's existing level
cancellation rule: while a cancelled child scope is exiting, if it must propagate
its cancellation because an unshielded cancelled ancestor is visible, that
ancestor can take responsibility for the child's cancellation. Uncancelled
intermediate scopes do not block this handoff. The child/intermediates do not
claim `cancelled_caught`; the responsible ancestor does. A shield that prevents
parent cancellation from being visible also prevents this handoff. Transfer only
the exiting scope's own cancellation leaves; foreign leaves cannot acquire
ownership through the handoff. A merely saved/replayed foreign exception is not
such a handoff.

**R4 — Preserve worker/callback transport and wrapping.** Correct cancellation
ownership must survive one or more nested `to_thread.run_sync()` /
`from_thread.run()` round trips, including multiple simultaneously live worker
threads. A replacement `asyncio.CancelledError` raised while handling an owned
cancellation can inherit its origin through `__context__`, as required for
framework wrappers. Use the first genuinely attributable cancellation encountered
from the outermost exception toward its context: a foreign attributable
cancellation must not borrow an older owned cancellation's identity. Do not lose
the cancellation or its meaningful context merely by formatting it as text for
the thread bridge. These rules concern in-process Python exception propagation;
cross-process serialization is not part of this version.

**R5 — Filter groups by ownership.** For nested `BaseExceptionGroup` values,
consume only leaves owned by the receiving scope (including legitimate R3
handoffs). Preserve foreign cancellation leaves, ordinary error leaves, their
order, remaining nesting, and group messages. Set `cancelled_caught` if this scope
actually consumes at least one owned leaf. Support either ordering of owned and
foreign branches.

**R6 — Respect live worker state.** A worker's `check_cancelled()` still chooses
the nearest visible cancelled scope and respects current shielding. With an
outer cancellation hidden by an inner shield it must return normally; when that
shield is disabled it must observe the outer cancellation. Distinct concurrent
operations must keep distinct scope associations. Reusing an idle worker for a
fresh uncancelled operation must not retain the previous operation's cancellation
state or make that old exception belong to the new scope.

**R7 — Retain cancellation reasons.** If the owning scope is cancelled with a
user reason, the cancellation seen from `check_cancelled()` must retain that
reason in its readable message. Repeating `cancel()` with another reason must not
replace the first request's reason. Exact formatting of any extra diagnostics is
not prescribed.

A representative R2 failure is a worker cancelling parent P and returning its
cancellation as a value, followed by code raising that exception inside a
separately cancelled shielded child C. P must consume its cancellation;
C must not. A representative R3 success is a child's cancellation unwinding
while its visible ancestor is cancelled: the ancestor must still handle it.
Both behaviors must hold, including when the exceptions travel through a worker
callback bridge or appear alongside foreign leaves in an exception group.