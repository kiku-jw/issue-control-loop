# Objective

- Build a deterministic GitHub-issue control loop for agent work.

# Scope

- Parse a PRD into a clean packet.
- Decide when a task needs GitHub, council, or a public diary.
- Classify issue-backed work into digest buckets.

# Acceptance Criteria

- The packet contains scope, acceptance criteria, and suggested tasks.
- The work shaper distinguishes tiny tasks from substantial work.
- The digest honors explicit operator review state.

# Data Contracts

- Marker comments use stable keys.

# Testing

- Unit tests cover PRD parsing and digest classification.

# Tasks

- [ ] Implement PRD parser
- [ ] Implement work shaper
- [ ] Implement digest logic
