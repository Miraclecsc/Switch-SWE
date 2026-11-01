Also, Finish the interruption edge on the consumer side. A receiver can be
cancelled after a receipt item is assigned to its wakeup container but before
receive() returns. That is not consumption: retain the item for another receiver
or a later receive, and leave send_and_wait pending until actual consumption.
If instead the receipt producer withdraws that assigned item, the awakened
consumer must keep waiting for a real item; it must not return the withdrawn
payload or report EOF while send channels remain open.

Use the original async API and real task/event coordination to test these races,
plus bounded fail_after task groups. A direct handoff recovered from a cancelled
consumer may need temporary retention even at capacity zero; it must remain
receivable exactly once. Do not
replace backend Event implementations to manufacture a race.