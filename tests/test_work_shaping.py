from issue_control_loop.work_shaping import classify_work


def test_tiny_fix_stays_light() -> None:
    result = classify_work(title="Fix typo", body="Change one typo in README and move on.")
    assert result["workSize"] == "tiny"
    assert result["tracking"] == "chat"
    assert result["publicationPotential"] == "none"


def test_public_workflow_becomes_public_draft() -> None:
    result = classify_work(
        title="Reusable workflow",
        body="""
This workflow turns a GitHub issue into a repeatable control loop.
It is reusable for other teams, has a CLI repo, and the main lesson is the tradeoff between chat and durable memory.
""",
    )
    assert result["publicationPotential"] == "public-draft"
    assert "public_artifact_anchor" in result["why"]
