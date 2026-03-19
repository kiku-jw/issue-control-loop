# Control Schema

The loop assumes one GitHub Issue stays canonical.

Comments carry machine-readable state:

- `issue-control-state`
- `issue-exec-plan`
- `issue-exec-run`
- `issue-prd-packet`

Legacy `openclaw-*` marker names are still read for backward compatibility, but new output should use the neutral `issue-*` names.

The issue body may also carry a light ops metadata block for durable hints.

The principle is simple:

- issue body = long-lived human intent
- marker comments = latest machine state
- project board = workflow lens

This separation keeps the issue readable while still making automation deterministic.
