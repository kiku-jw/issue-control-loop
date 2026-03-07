# GitHub Mobile as an operator surface

`issue-control-loop` treats GitHub as the durable control layer.

That gets more interesting once you stop thinking only about desktop use.

## The useful split

- `Issue` stores canonical task meaning and machine-readable state.
- `Project` shows the queue, priority, owner, and workflow stage.
- `GitHub Mobile` lets you inspect and nudge that state from a phone.
- chat tools like Telegram stay useful for pings, not for being the only memory layer.

This split keeps each surface honest.

## What this gives you on a phone

If you keep one issue canonical, the GitHub app on your phone becomes surprisingly capable:

- see whether the task is blocked, running, or waiting for review
- read the brief without hunting through old chats
- open the latest branch, commit, or PR directly from the issue
- move a Project card or leave a comment while away from the laptop

That is not “full remote coding.”

It is better: fast remote supervision.

## Where official GitHub is already going

As of March 7, 2026, GitHub’s own docs say:

- GitHub Copilot is available in GitHub Mobile
- you can ask Copilot questions about a repository, file, issue, or PR from GitHub Mobile
- you can assign an issue to Copilot from GitHub Mobile
- the issue-assignment API supports `target_repo`, `base_branch`, `custom_instructions`, `custom_agent`, and `model`

So the platform itself is converging on the same pattern:

`issue = prompt + context + control handle`

## How to use this repo with that pattern

For a phone-friendly loop, keep these fields explicit:

1. The issue body must explain the goal in plain language.
2. The PRD packet or short execution brief must be easy to skim.
3. The latest machine state must live in marker comments, not only in chat.
4. The Project should have fields that answer operator questions quickly:
   - priority
   - status
   - type
   - owner
   - next decision

If those are missing, mobile control becomes guesswork.

## Current stance for our stack

For our own system today, GitHub is best used as:

- canonical task memory
- project board and operator dashboard
- mobile oversight layer

Telegram is still better for:

- short live pings
- back-and-forth decisions
- quick “continue / pause / explain” control

The important part is not choosing one app.

The important part is making sure they do not compete for the same truth.

## Good next steps

- keep the issue canonical
- keep the project board derived and readable on mobile
- keep comments short and explicit
- only automate phone-triggered actions that are narrow and reversible

If you do that, phone control starts helping instead of becoming another source of chaos.

## Sources

- [GitHub Copilot plans & pricing](https://github.com/features/copilot/plans)
- [Asking GitHub Copilot questions in GitHub Mobile](https://docs.github.com/en/copilot/github-copilot-chat/copilot-chat-in-github-mobile/using-github-copilot-chat-in-github-mobile)
- [Assigning an issue to Copilot](https://docs.github.com/copilot/how-tos/use-copilot-agents/coding-agent/assign-copilot-to-an-issue)
- [Managing coding agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/manage-agents)
- [Creating custom agents for Copilot coding agent](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [GitHub Projects как память для AI-агента](https://sereja.tech/blog/github-projects-ai-agent-memory/)
- [Личная корпорация: сотрудники живут в компьютере](https://sereja.tech/blog/personal-corporation-event-driven-agents/)
- [Документируй разговоры с агентом, а не код](https://sereja.tech/blog/document-conversations-not-code/)
