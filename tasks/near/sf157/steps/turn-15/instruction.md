Please check this too: This is the only thing it returns, might as well use it as a return type hint?

Discovery via dir() on either module must list both spellings without emitting warnings. Repeated alias access must continue to warn, with the warning attributed to the caller. Unknown names must still raise AttributeError.