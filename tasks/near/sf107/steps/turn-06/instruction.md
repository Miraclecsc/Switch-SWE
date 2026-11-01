One more thing: I see `KeyTransformExact` doesn't have it (at least not until Django 7.) I also see this logic that doesn't treat `exact` and `iexact` equivalently:

On SQLite, an explicit Value(None, output_field=JSONField()) RHS must have the same JSON-null meaning for key-path exact and iexact as a literal None RHS. Preserve path parameters and prior requirements.