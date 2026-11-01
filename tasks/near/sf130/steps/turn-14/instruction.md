One more thing: Correct, thanks! (I used `self.t.year - 1000` though)

Verify per-form field isolation: refreshing a deep-copied field or one bound form instance must not mutate another instance or the declared base field. Repeated successful refreshes replace rather than append choices, remove vanished files, and keep field and widget choices synchronized.