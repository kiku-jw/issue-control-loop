from pathlib import Path

from issue_control_loop.sequence import build_execution_sequence
from issue_control_loop.sequence import write_artifacts


PRD_TEXT = """
# Goal

- Ship a deterministic PRD-to-execution lane.

# Scope

- Parse the PRD.
- Create the implementation plan.
- Break execution into issue tasks.

# Acceptance Criteria

- Codex can tell what comes next without inventing a new flow.

# Testing

- Add unit tests for the new sequence builder.
"""


def test_substantial_prd_prefers_issue_surface_when_github_available() -> None:
    result = build_execution_sequence(
        title="Execution lane",
        body=PRD_TEXT,
        source={"type": "markdown_file", "path": "/tmp/prd.md"},
        github_mode="available",
    )
    assert result["inputKind"] == "structured-prd"
    assert result["workSize"] == "substantial"
    assert result["canonicalSource"] == "github-issue"
    assert result["executionSurface"] == "github-issue"
    assert result["orderedSteps"][1]["key"] == "create-or-update-issue"
    assert any(step["key"] == "create-or-update-issue" for step in result["orderedSteps"])
    assert result["artifacts"]["issueMarkdown"] is not None
    assert "openclaw-ops-meta:start" in result["artifacts"]["issueMarkdown"]
    assert result["artifacts"]["paths"]["plan"].startswith("docs/plans/")
    assert result["artifacts"]["paths"]["issue"].startswith("docs/issues/")


def test_substantial_prd_can_fall_back_to_checked_in_docs_without_github() -> None:
    result = build_execution_sequence(
        title="Execution lane",
        body=PRD_TEXT,
        source={"type": "markdown_file", "path": "/tmp/prd.md"},
        github_mode="unavailable",
    )
    assert result["canonicalSource"] == "checked-in-execution-surface"
    assert result["executionSurface"] == "checked-in-plan-status-test-plan"
    assert any(step["key"] == "use-checked-in-execution-surface" for step in result["orderedSteps"])
    assert result["artifacts"]["issueMarkdown"] is None


def test_tiny_work_stays_light() -> None:
    result = build_execution_sequence(
        title="Fix typo",
        body="Change one typo in README and verify the file still looks correct.",
        source={"type": "text"},
        github_mode="available",
    )
    assert result["workSize"] == "tiny"
    assert result["canonicalSource"] == "chat"
    assert result["executionSurface"] == "chat"
    assert result["nextAction"] == "keep-work-light"
    assert result["orderedSteps"][0]["title"] == "Keep the work light"


def test_sequence_always_returns_plan_status_and_test_plan_scaffolds() -> None:
    result = build_execution_sequence(
        title="Execution lane",
        body=PRD_TEXT,
        source={"type": "markdown_file", "path": "/tmp/prd.md"},
        github_mode="available",
    )
    assert result["artifacts"]["planMarkdown"].startswith("# Plans")
    assert result["artifacts"]["statusMarkdown"].startswith("# Status")
    assert result["artifacts"]["testPlanMarkdown"].startswith("# Test Plan")


def test_write_artifacts_creates_files(tmp_path: Path) -> None:
    result = build_execution_sequence(
        title="Execution lane",
        body=PRD_TEXT,
        source={"type": "markdown_file", "path": "/tmp/prd.md"},
        github_mode="available",
    )
    written = write_artifacts(result, root_dir=tmp_path)
    assert Path(written["plan"]).exists()
    assert Path(written["status"]).exists()
    assert Path(written["testPlan"]).exists()
    assert Path(written["issue"]).exists()
    assert Path(written["opsStateComment"]).exists()
    assert Path(written["execPlanComment"]).exists()
    assert Path(written["sequenceJson"]).exists()
