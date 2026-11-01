Also, Maybe we can add what constitutes "quick succession"? i.e. mention the 500ms.

Extend the click-chain behavior: continuing a chain requires the same actual widget object, mouse button, modifier combination, screen position, and existing time threshold. Replacing a widget at the same coordinates must start a new chain. Preserve chain values through Click.from_event and offset handling.