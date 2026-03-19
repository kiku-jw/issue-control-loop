"""Build an ordered execution sequence from raw task input or a PRD."""

from __future__ import annotations

from datetime import date
import json
import re
from pathlib import Path
from typing import Any

from .control_schema import (
    OPS_BODY_MARKER_END,
    OPS_BODY_MARKER_START,
    render_marker_comment,
)
from .prd import normalize_markdown, parse_prd_text
from .work_shaping import classify_work


SEQUENCE_VERSION = 1
SECTION_KEYS = (
    "objective",
    "scope",
    "constraints",
    "acceptanceCriteria",
    "dataContracts",
    "testing",
    "openQuestions",
    "suggestedTasks",
)


def detect_input_kind(packet: dict[str, Any]) -> str:
    populated = sum(bool(packet.get(key)) for key in SECTION_KEYS)
    if populated >= 4:
        return "structured-prd"
    if populated >= 2:
        return "loose-spec"
    return "task-text"


def step(*, key: str, title: str, artifact: str, why: str) -> dict[str, str]:
    return {"key": key, "title": title, "artifact": artifact, "why": why}


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-") or "task"


def bullet_lines(items: list[str], *, fallback: str = "TBD") -> list[str]:
    if not items:
        return [f"- {fallback}"]
    return [f"- {item}" for item in items]


def numbered_step_lines(items: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item['title']} (`{item['key']}`)")
    return lines


def build_artifacts(
    *,
    title: str,
    sequence: dict[str, Any],
    prd_packet: dict[str, Any],
) -> dict[str, Any]:
    today = date.today().isoformat()
    slug = slugify(title)
    plan_path = f"docs/plans/{today}-{slug}.md"
    status_path = "docs/status.md"
    test_plan_path = "docs/test-plan.md"
    issue_path = f"docs/issues/{today}-{slug}.md"
    staging_dir = f".issue-control-loop/{slug}"

    issue_markdown: str | None = None
    ops_state_comment: str | None = None
    exec_plan_comment: str | None = None

    if sequence["executionSurface"] in {"github-issue", "existing-github-issue"}:
        issue_lines = [
            f"# {title}",
            "",
            "## Objective",
            *bullet_lines(prd_packet.get("objective") or [], fallback="Clarify the objective."),
            "",
            "## Scope",
            *bullet_lines(prd_packet.get("scope") or [], fallback="Clarify scope before execution."),
            "",
            "## Acceptance Criteria",
            *bullet_lines(prd_packet.get("acceptanceCriteria") or [], fallback="Add acceptance criteria."),
            "",
            "## Suggested Tasks",
            *bullet_lines(prd_packet.get("suggestedTasks") or [], fallback="Break work into executable tasks."),
            "",
            "## Ordered Workflow",
            *numbered_step_lines(sequence["orderedSteps"]),
            "",
                "## Suggested Execution Surface",
                f"- Issue path: `{issue_path}`",
                f"- Plan path: `{plan_path}`",
                f"- Status path: `{status_path}`",
                f"- Test plan path: `{test_plan_path}`",
                "",
            OPS_BODY_MARKER_START,
            "{",
            '  "schemaVersion": 1,',
            '  "state": "planned",',
            '  "executor": "codex_local",',
            '  "needsHumanDecision": false',
            "}",
            OPS_BODY_MARKER_END,
            "",
        ]
        issue_markdown = "\n".join(issue_lines)
        ops_state_comment = render_marker_comment(
            "ops_state",
            {
                "schemaVersion": 1,
                "state": "planned",
                "executor": "codex_local",
                "updatedAt": today,
            },
        )
        exec_plan_comment = render_marker_comment(
            "exec_plan",
            {
                "schemaVersion": 1,
                "planPath": plan_path,
                "statusPath": status_path,
                "testPlanPath": test_plan_path,
                "nextAction": sequence["nextAction"],
            },
        )

    suggested_tasks = prd_packet.get("suggestedTasks") or []
    milestone_lines = [
        "| ID | Title | Depends on | Status |",
        "| --- | --- | --- | --- |",
    ]
    if suggested_tasks:
        for index, task in enumerate(suggested_tasks, start=1):
            depends_on = "-" if index == 1 else f"M{index - 1}"
            milestone_lines.append(f"| M{index} | {task} | {depends_on} | [ ] |")
    else:
        milestone_lines.append("| M1 | First reversible slice | - | [ ] |")

    plan_markdown = "\n".join(
        [
            "# Plans",
            "",
            "## Source",
            f"- Task: {title}",
            f"- Canonical input: {prd_packet['source']['type']}",
            "- Repo context: TBD",
            f"- Last updated: {today}",
            "",
            "## Assumptions",
            "- TBD",
            "",
            "## Milestone Order",
            *milestone_lines,
            "",
            "## Definition of Done",
            *bullet_lines(prd_packet.get("acceptanceCriteria") or [], fallback="Add done conditions."),
            "",
            "## Validation",
            "- Add exact commands before execution.",
            "",
        ]
    )

    status_markdown = "\n".join(
        [
            "# Status",
            "",
            "## Snapshot",
            "- Current phase: planning",
            f"- Plan file: `{plan_path}`",
            "- Status: yellow",
            f"- Last updated: {today}",
            "",
            "## Done",
            "- none",
            "",
            "## In Progress",
            f"- {sequence['orderedSteps'][0]['title']}",
            "",
            "## Next",
            f"- `{sequence['nextAction']}`",
            "",
            "## Commands",
            "```sh",
            "# add repo-specific validation commands",
            "```",
            "",
        ]
    )

    test_plan_markdown = "\n".join(
        [
            "# Test Plan",
            "",
            "## Source",
            f"- Task: {title}",
            f"- Plan file: `{plan_path}`",
            f"- Status file: `{status_path}`",
            f"- Last updated: {today}",
            "",
            "## Validation Scope",
            "- In scope:",
            *bullet_lines(prd_packet.get("scope") or [], fallback="Clarify scope."),
            "- Out of scope:",
            "- TBD",
            "",
            "## Acceptance Gates",
            "- [ ] lint",
            "- [ ] test",
            "- [ ] build",
            "- [ ] smoke",
            "",
            "## Open Risks",
            *bullet_lines(prd_packet.get("openQuestions") or [], fallback="None recorded yet."),
            "",
        ]
    )

    return {
        "paths": {
            "issue": issue_path,
            "plan": plan_path,
            "status": status_path,
            "testPlan": test_plan_path,
            "stagingDir": staging_dir,
        },
        "issueMarkdown": issue_markdown,
        "opsStateComment": ops_state_comment,
        "execPlanComment": exec_plan_comment,
        "planMarkdown": plan_markdown,
        "statusMarkdown": status_markdown,
        "testPlanMarkdown": test_plan_markdown,
    }


def build_execution_sequence(
    *,
    title: str,
    body: str,
    source: dict[str, Any],
    github_mode: str = "available",
) -> dict[str, Any]:
    if github_mode not in {"available", "existing-issue", "unavailable"}:
        raise ValueError(f"Unsupported github_mode: {github_mode}")

    normalized = normalize_markdown(body)
    prd_packet = parse_prd_text(title=title, body=normalized, source=source)
    shape = classify_work(title=title, body=normalized, source=source)
    input_kind = detect_input_kind(prd_packet)
    has_execution_signal = bool(
        prd_packet.get("scope")
        or prd_packet.get("acceptanceCriteria")
        or prd_packet.get("suggestedTasks")
        or prd_packet.get("testing")
    )

    effective_work_size = shape["workSize"]
    effective_tracking = shape["tracking"]
    effective_review_mode = shape["reviewMode"]
    effective_brief_mode = shape["briefMode"]

    if input_kind in {"structured-prd", "loose-spec"} and has_execution_signal:
        effective_work_size = "substantial"
        effective_brief_mode = "execution-brief"
        if effective_review_mode == "none":
            effective_review_mode = "operator-review"
        if github_mode in {"available", "existing-issue"}:
            effective_tracking = "github-issue"
        else:
            effective_tracking = "local-note"

    steps: list[dict[str, str]] = []
    execution_surface = effective_tracking
    canonical_source = "chat"

    if effective_work_size == "tiny":
        if effective_tracking == "chat":
            execution_surface = "chat"
        else:
            execution_surface = "lightweight-note"
        canonical_source = execution_surface

        steps.append(
            step(
                key="keep-work-light",
                title="Keep the work light",
                artifact="chat task or lightweight note",
                why="Tiny work should not be inflated into issue-heavy process.",
            )
        )
        if effective_brief_mode == "lightweight-checklist":
            steps.append(
                step(
                    key="write-lightweight-checklist",
                    title="Write a lightweight checklist",
                    artifact="small checklist",
                    why="A short checklist is enough to keep execution honest for small work.",
                )
            )
        steps.extend(
            [
                step(
                    key="implement-smallest-slice",
                    title="Implement the smallest safe slice",
                    artifact="minimal code or content change",
                    why="Tiny work should move straight to the smallest reversible step.",
                ),
                step(
                    key="verify",
                    title="Verify with a real check",
                    artifact="fresh command output or smoke evidence",
                    why="No completion claims without fresh verification.",
                ),
                step(
                    key="report-result",
                    title="Report the result",
                    artifact="concise summary with evidence",
                    why="Close the loop without creating extra ceremony.",
                ),
            ]
        )
    else:
        if github_mode == "existing-issue":
            execution_surface = "existing-github-issue"
            canonical_source = "github-issue"
        elif github_mode == "available":
            execution_surface = "github-issue"
            canonical_source = "github-issue"
        else:
            execution_surface = "checked-in-plan-status-test-plan"
            canonical_source = "checked-in-execution-surface"

        steps.extend(
            [
                step(
                    key="refresh-product-truth",
                    title="Refresh product truth",
                    artifact="updated PRD or explicit assumptions",
                    why="The PRD is living product truth, not a frozen prompt blob.",
                ),
            ]
        )

        if github_mode == "existing-issue":
            steps.append(
                step(
                    key="update-current-issue",
                    title="Update the current GitHub issue",
                    artifact="issue body or issue breakdown",
                    why="Substantial work should execute from the current issue instead of from the raw PRD.",
                )
            )
        elif github_mode == "available":
            steps.append(
                step(
                    key="create-or-update-issue",
                    title="Create or update the GitHub issue",
                    artifact="canonical issue and issue breakdown",
                    why="GitHub is the durable execution lane for substantial work.",
                )
            )
        else:
            steps.append(
                step(
                    key="use-checked-in-execution-surface",
                    title="Use checked-in execution docs as the lane",
                    artifact="plan/status/test-plan as canonical surface",
                    why="When GitHub is unavailable, checked-in docs temporarily carry the execution loop.",
                )
            )

        steps.extend(
            [
                step(
                    key="create-implementation-plan",
                    title="Create the implementation plan",
                    artifact="execution brief or implementation plan",
                    why="Execution should run from a plan, not directly from raw PRD input.",
                ),
                step(
                    key="write-status-and-test-plan",
                    title="Write status and test plan",
                    artifact="status.md and test-plan.md",
                    why="Durable status and validation surfaces reduce chat-only drift.",
                ),
            ]
        )

        steps.extend(
            [
                step(
                    key="execute-first-slice",
                    title="Execute the first reversible slice",
                    artifact="first milestone or issue task result",
                    why="Start with the first bounded slice that can produce evidence.",
                ),
                step(
                    key="verify",
                    title="Verify with real checks",
                    artifact="test, build, or smoke evidence",
                    why="Verification decides whether the slice is real, not confidence.",
                ),
                step(
                    key="sync-back",
                    title="Sync result back to the durable surface",
                    artifact="updated issue, status, and PRD if truth changed",
                    why="Durable surfaces must reflect reality after each meaningful slice.",
                ),
            ]
        )

    result = {
        "sequenceVersion": SEQUENCE_VERSION,
        "title": title,
        "source": source,
        "inputKind": input_kind,
        "githubMode": github_mode,
        "workSize": effective_work_size,
        "tracking": effective_tracking,
        "canonicalSource": canonical_source,
        "reviewMode": effective_review_mode,
        "briefMode": effective_brief_mode,
        "executionSurface": execution_surface,
        "highRisk": shape["highRisk"],
        "prdPacket": prd_packet,
        "orderedSteps": steps,
        "nextAction": steps[0]["key"],
    }
    result["artifacts"] = build_artifacts(title=title, sequence=result, prd_packet=prd_packet)
    return result


def write_artifacts(sequence: dict[str, Any], *, root_dir: str | Path) -> dict[str, str]:
    root = Path(root_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    artifacts = sequence["artifacts"]
    written: dict[str, str] = {}

    def write_relative(key: str, relative_path: str, content: str | None) -> None:
        if not content:
            return
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written[key] = str(destination)

    write_relative("plan", artifacts["paths"]["plan"], artifacts["planMarkdown"])
    write_relative("status", artifacts["paths"]["status"], artifacts["statusMarkdown"])
    write_relative("testPlan", artifacts["paths"]["testPlan"], artifacts["testPlanMarkdown"])
    write_relative("issue", artifacts["paths"]["issue"], artifacts.get("issueMarkdown"))

    staging_dir = artifacts["paths"]["stagingDir"]
    write_relative("opsStateComment", f"{staging_dir}/ops-state-comment.md", artifacts.get("opsStateComment"))
    write_relative("execPlanComment", f"{staging_dir}/exec-plan-comment.md", artifacts.get("execPlanComment"))
    write_relative(
        "sequenceJson",
        f"{staging_dir}/sequence.json",
        json.dumps(sequence, ensure_ascii=False, indent=2),
    )
    return written


def render_markdown(sequence: dict[str, Any], *, emit_artifacts: bool = False) -> str:
    lines = [
        f"# Execution Sequence: {sequence['title']}",
        "",
        f"- Input kind: `{sequence['inputKind']}`",
        f"- Work size: `{sequence['workSize']}`",
        f"- GitHub mode: `{sequence['githubMode']}`",
        f"- Execution surface: `{sequence['executionSurface']}`",
        f"- Canonical source: `{sequence['canonicalSource']}`",
        f"- Next action: `{sequence['nextAction']}`",
        "",
        "## Ordered Steps",
        "",
    ]
    for index, item in enumerate(sequence["orderedSteps"], start=1):
        lines.append(f"{index}. **{item['title']}**")
        lines.append(f"   Artifact: `{item['artifact']}`")
        lines.append(f"   Why: {item['why']}")

    if emit_artifacts:
        artifacts = sequence.get("artifacts") or {}
        lines.extend(
            [
                "",
                "## Suggested Paths",
                "",
                f"- Issue: `{artifacts['paths']['issue']}`",
                f"- Plan: `{artifacts['paths']['plan']}`",
                f"- Status: `{artifacts['paths']['status']}`",
                f"- Test plan: `{artifacts['paths']['testPlan']}`",
                "",
                "## Issue Markdown",
                "",
                "```md",
                artifacts.get("issueMarkdown") or "<no issue scaffold for this lane>",
                "```",
                "",
                "## Plan Markdown",
                "",
                "```md",
                artifacts["planMarkdown"],
                "```",
                "",
                "## Status Markdown",
                "",
                "```md",
                artifacts["statusMarkdown"],
                "```",
                "",
                "## Test Plan Markdown",
                "",
                "```md",
                artifacts["testPlanMarkdown"],
                "```",
            ]
        )

    lines.append("")
    return "\n".join(lines)
