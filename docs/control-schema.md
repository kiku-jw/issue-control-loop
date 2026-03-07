# Control Schema

The loop assumes one GitHub Issue stays canonical.

Comments carry machine-readable state:

- `openclaw-ops-state`
- `openclaw-exec-plan`
- `openclaw-executor-run`
- `openclaw-prd-packet`

The issue body may also carry a light ops metadata block for durable hints.

The principle is simple:

- issue body = long-lived human intent
- marker comments = latest machine state
- project board = workflow lens

This separation keeps the issue readable while still making automation deterministic.
