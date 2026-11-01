And here, Should we link the `jinja2.Environment` documentation, or no need?

Reject env combined with directory or any legacy environment option by raising ValueError before mutating the supplied environment. Keep directory-only legacy options supported with their deprecation warning. Custom environment rendering must remain reusable across requests and preserve caller-configured globals.