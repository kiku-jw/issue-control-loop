---
name: issue-control-loop
description: Turn a GitHub Issue into a clean human-agent control loop with canonical issue state, deterministic PRD intake, work shaping, and explicit handoff points.
---

# Issue Control Loop

Use this skill when GitHub should be the durable task surface instead of leaving work trapped in chat.

Typical prompts:

- `turn this GitHub issue into a control loop`
- `use the issue as the canonical handoff surface`
- `parse this PRD and make it issue-ready`
- `shape this task before we over-process it`
- `set up explicit issue state for humans and agents`

## What to do

1. Decide if the work deserves an issue-centric loop.
   - For tiny local work, keep things lighter.
2. Use the CLI primitives that match the task:

```bash
issue-control-loop prd --markdown-file /absolute/path/to/prd.md --format markdown
issue-control-loop shape --text "Task description here" --format markdown
```

3. Keep the issue body human-readable and durable.
4. Keep machine state explicit in marker comments, not implied in chat.
5. Treat Projects as the workflow lens, not the only source of truth.

## When to read the docs

Read `docs/control-schema.md` when you need the marker-comment layout.

Read `docs/mobile-control-surface.md` when the user cares about GitHub Mobile, phone-first control, or GitHub as an operator surface.

## Rules

- One canonical issue beats scattered state across chat and boards.
- Machine-readable state must be explicit.
- Tiny work should stay light.
- Use this skill to clarify handoff and control, not to add ceremony for its own sake.
