And here, PEP 484 is pretty clear on this. A plain `tuple` which I had here, is equivalent to `Tuple[Any]` which is NOT the same as `Tuple[object]`.

Reading up on it once more, it's not so *clear* why this is so, but the `Any` type was introduced specifically for this purpose.