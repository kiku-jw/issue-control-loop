# issue-control-loop

Turn a GitHub Issue into a clean handoff point between planning, coding, review, and human control.

This repo packages the deterministic core of that loop:

- marker-comment control schema
- PRD intake
- work shaping
- task digest classification

It does not hardcode Telegram, local paths, topic ids, or any one deployment stack.

## Why this exists

Most agent workflows fail in one of two boring ways:

- everything stays trapped in chat
- or everything turns into process theatre

`issue-control-loop` aims for the middle: keep one issue canonical, keep machine state explicit, and keep the human in the loop without turning every task into paperwork.

## What is in this repo

- `issue_control_loop.control_schema`
  - marker constants
  - parsing and merging helpers for issue body + comment state
- `issue_control_loop.prd`
  - deterministic PRD parser
  - lightweight workflow hints
- `issue_control_loop.work_shaping`
  - classify work into tiny vs substantial
  - recommend tracking, brief, review, and publication mode
- `issue_control_loop.digest`
  - classify project items into ready/in-progress/waiting/review/problem buckets

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
pytest -q
```

Parse a PRD:

```bash
issue-control-loop prd --markdown-file examples/prd-example.md --format markdown
```

Shape a task before you over-process it:

```bash
issue-control-loop shape --text "We need a reusable workflow that turns a GitHub issue into an agent control loop." --format markdown
```

## Design rules

- GitHub Issue is canonical.
- Project is a board view, not the only source of truth.
- Machine state must live in explicit marker comments, not vibes.
- Tiny work should stay light.
- Public writing should start from a public-safe artifact, not private kitchen.

## Why Projects matter beyond memory

Projects are not only a nicer backlog view.

They give you an operator layer on top of issue-backed agent work:

- one place to see what is ready, blocked, in progress, or waiting for review
- custom fields such as priority, effort, type, owner, or next decision
- cross-repo visibility without copying tasks into a second system
- a clean split between canonical task state (`Issue`) and board state (`Project`)

That matters even more once several agents touch the same product. Chat is still useful for signals. Projects make it obvious what is actually happening.

## Why this is useful from a phone

Once issue + project become canonical, the GitHub app stops being “just notifications.”

It becomes a lightweight control surface:

- open the issue and see the real task context
- scan the project board to understand what needs attention
- jump from issue to branch, commit, or PR
- leave a comment or move a card without opening a laptop

This repo does not depend on GitHub Mobile. But it is built to make phone control sane instead of accidental.

## Where Copilot fits

GitHub itself is moving in the same direction.

As of March 7, 2026, GitHub documents that you can:

- ask Copilot repository, issue, PR, and code questions in GitHub Mobile
- assign an issue to Copilot from GitHub Mobile
- customize issue assignment via API with target repo, base branch, custom instructions, custom agent, and model

That does not replace a self-hosted control plane. But it makes GitHub a stronger universal handoff surface for both humans and agents.

See [docs/mobile-control-surface.md](docs/mobile-control-surface.md) for the practical operator pattern.

## What is intentionally missing

- GitHub API adapter
- Telegram notifier
- local executor runner

Those adapters vary a lot by environment. The core logic here stays portable on purpose.
