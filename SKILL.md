---
name: issue-control-loop
description: Turn a GitHub Issue into a clean human-agent control loop with canonical issue state, deterministic PRD intake, explicit machine markers, and clear handoff points. Use when GitHub should be the durable control surface instead of chat alone.
---

# Issue Control Loop

## Metadata
- Trigger when: the work deserves an issue-centric control loop, PRD intake, or explicit human-agent handoff state.
- Do not use when: the task is tiny local work that would become slower with issue overhead.

## Skill Purpose

Make the issue the durable task surface so humans and agents can coordinate from explicit state instead of reconstructing intent from chat.

## Instructions
1. Decide first whether the work is substantial enough for an issue-centric loop. If not, keep it lighter and stop there.
2. Use the CLI primitives that match the task, such as `issue-control-loop prd --markdown-file /absolute/path/to/prd.md --format markdown` or `issue-control-loop shape --text "Task description here" --format markdown`. Read `/Users/nick/.codex/skills/issue-control-loop/README.md` for the current CLI and marker conventions if you need exact details.
3. Keep the issue body human-readable and machine state explicit in marker comments or other deterministic structure. Treat Projects as the workflow lens, not as the only source of truth. If another skill should take over next, name it explicitly with a one-line reason.

## Non-Negotiable Acceptance Criteria
- One canonical issue beats scattered state across chat and boards.
- Machine-readable state must be explicit, not implied.
- Tiny work stays light; this skill does not exist to add ceremony.
- The final issue state names the next handoff point clearly enough for another human or agent run to continue.

## Output
- Issue-ready markdown or updated issue state with explicit machine markers.
- The command or workflow used to generate that state.
- A short note on the next human or agent handoff step.
- `Next skill options` (only if needed): `$work-shaping` — decide how much process the issue deserves; `$spec-bundle` — add contracts/schema/test artifacts when the issue is too soft; `$justdoit` — turn the issue into live plan/status/test-plan files.
