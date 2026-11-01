And here, Add cancellation and close semantics to send_and_wait.

If cancellation reaches that call before its item is consumed, withdraw only
that operation's item, propagate cancellation, and leave other items in order.
This applies both to a queued sender and to an item already admitted into the
buffer or assigned to a receiver that has not resumed. Withdrawal must free its
buffer slot and admit/unblock the next FIFO sender without requiring an extra
receive. Do not compare user payloads for equality to identify an operation.

If consumption has already happened, successful delivery wins a simultaneous
cancellation or last-receiver close even if the producer has not resumed:
send_and_wait returns normally and must not duplicate/retract the consumed item.
Closing one receive clone does not break pending receipts while another remains
open. Closing the last receiver before consumption must promptly raise
BrokenResourceError for pending send_and_wait calls, buffered or queued.
New calls on a closed sending handle raise ClosedResourceError; its open clones
remain usable. These rules extend, rather than replace, the preceding stages.