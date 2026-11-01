Also, We are missing the same in `WebSockets`.

Carry the HTTPConnection state type parameter through WebSocket as well as Request, so WebSocket[StateType] is usable without changing runtime scope-state aliasing.