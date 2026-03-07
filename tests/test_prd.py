from issue_control_loop.prd import parse_prd_text


PRD_TEXT = """
# Objective

- Ship a clean PRD intake path.

# Scope

- Parse GitHub issue PRDs.
- Emit one execution packet.

# Acceptance Criteria

- Packet includes scope and acceptance criteria.

# Data Contracts

- Packet schema version is stable.

# Testing

- Unit tests cover malformed markdown.

# Tasks

- [ ] Build deterministic parser
- [ ] Add tests
"""


def test_parse_prd_extracts_core_sections() -> None:
    packet = parse_prd_text(
        title="PRD Intake",
        body=PRD_TEXT,
        source={"type": "markdown_file", "path": "/tmp/prd.md"},
    )
    assert packet["prdPacketVersion"] == 1
    assert "Ship a clean PRD intake path." in packet["objective"][0]
    assert "Packet includes scope and acceptance criteria." in packet["acceptanceCriteria"][0]
    assert packet["suggestedTasks"] == ["Build deterministic parser", "Add tests"]
    assert packet["workflowHint"]["recommendedTracking"] == "create_or_use_github_issue"
