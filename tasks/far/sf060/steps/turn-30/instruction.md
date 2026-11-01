One more thing: Hmm to make result get garbage collected we can pass a boxed [result] and just.pop() to get it. The other option is to run a checkpoint in the tests

Finish the same implementation with bounded weak-reference regression checks for completed and abandoned work items. Account for the event loop's completed-future lifetime before checking collection; do not change user return values into boxes or require an extra user work item to release Context state.
Implement and validate this.