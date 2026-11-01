And here, I don't know what's deprecation policy but are you sure raise error here. isn't it breaking change for those using `app`.

Deprecate app based on its presence (app is not None), without consulting its truth value. Valid callable WSGI/ASGI applications may be falsey or reject boolean conversion; they must still warn and remain usable. Passing app=None must not warn about app.