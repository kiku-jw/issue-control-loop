from issue_control_loop.digest import ProjectItem, build_digest, classify_item


def test_ready_to_start_classification() -> None:
    item = ProjectItem(
        item_id="pvti_1",
        issue_repo="acme/ops",
        issue_number=10,
        issue_url="https://github.com/acme/ops/issues/10",
        title="Build task",
        status="Todo",
        approval="Approved",
        destination="Build",
        kind="Task",
        priority="P1",
    )
    result = classify_item(item, issue_body="PRD body", comments=None)
    assert result["section"] == "readyToStart"


def test_comment_ops_state_overrides_issue_body() -> None:
    item = ProjectItem(
        item_id="pvti_2",
        issue_repo="acme/ops",
        issue_number=11,
        issue_url="https://github.com/acme/ops/issues/11",
        title="Awaiting review",
        status="Todo",
        approval="Needs Review",
        destination="Build",
        kind="Task",
        priority="P2",
    )
    result = classify_item(
        item,
        issue_body="""Body

<!-- issue-control-meta:start -->
{"state":"ready","executor":"codex_local"}
<!-- issue-control-meta:end -->
""",
        comments=[
            {
                "body": """<!-- issue-control-state:start -->
{"schemaVersion":1,"state":"awaiting_review","owner":"Nick","updatedAt":"2026-03-07T12:00:00Z"}
<!-- issue-control-state:end -->"""
            }
        ],
    )
    assert result["section"] == "waitingOnOperator"
    assert result["reason"] == "awaiting operator review"


def test_digest_counts_sections() -> None:
    digest = build_digest(
        [
            {
                "section": "readyToStart",
                "item": {"priority": "P1", "issueNumber": 10},
                "reason": "approved build work",
            }
        ]
    )
    assert digest["summary"]["readyToStart"] == 1
    assert digest["summary"]["scanned"] == 1
