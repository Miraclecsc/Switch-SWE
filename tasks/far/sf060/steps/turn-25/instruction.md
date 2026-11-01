Also, Thanks to your suggestion. `gc.collect()` works. Now only the timeout problem in the CI/CD.

Apply those ownership rules to abandon_on_cancel=True as well. Cancellation may abandon the await, but must not clear the Context out from under the running thread; after the thread actually finishes, its snapshot is released and no result is delivered back to the cancelled awaiter.
Implement and validate this.