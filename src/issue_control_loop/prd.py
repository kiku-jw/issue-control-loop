"""Deterministic PRD parsing."""

from __future__ import annotations

import re
from typing import Any


PACKET_VERSION = 1
SUBSTANTIAL_SIGNAL_PATTERNS = (
    (r"\bmigration\b|\bschema\b|\bdata contract\b|\bapi contract\b", "touches_schema_or_contracts"),
    (r"\bdependency\b|\bnpm install\b|\bpip install\b|\bpackage\b", "adds_or_changes_dependencies"),
    (r"\brollout\b|\bdeploy\b|\bwebhook\b|\brate limit\b|\bbackground worker\b|\bqueue\b", "has_rollout_or_backend_risk"),
    (r"\bauth\b|\bpermission\b|\brls\b|\bstorage\b|\bupload\b", "touches_security_or_access_boundaries"),
)
SECTION_PATTERNS = {
    "objective": [r"\bobjective\b", r"\bgoal\b", r"\bproblem\b", r"\bwhy\b", r"\bцель\b", r"\bпроблем"],
    "scope": [r"\bscope\b", r"\bin scope\b", r"\bout of scope\b", r"\bграниц", r"\bобъем\b"],
    "constraints": [r"\bconstraint", r"\bnon-goal", r"\blimit", r"\brisk", r"\bогранич", r"\bне цель\b"],
    "acceptanceCriteria": [r"\bacceptance\b", r"\bdefinition of done\b", r"\bsuccess criteria\b", r"\bкритерии\b", r"\bdone\b"],
    "dataContracts": [r"\bdata\b", r"\bcontract\b", r"\bschema\b", r"\bapi\b", r"\bmodel\b", r"\bсхем", r"\bконтракт"],
    "testing": [r"\btest", r"\bqa\b", r"\bverification\b", r"\bпровер", r"\bтест"],
    "openQuestions": [r"\bopen question", r"\bunknown", r"\bquestion", r"\bdecision", r"\bвопрос", r"\bнеяс"],
    "tasks": [r"\btask", r"\bimplementation plan\b", r"\bstep", r"\bchecklist\b", r"\btodo\b", r"\bэтап", r"\bшаг", r"\bчеклист"],
}


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("\n---\n", 1)
    return parts[1] if len(parts) == 2 else text


def normalize_markdown(text: str) -> str:
    return strip_frontmatter(text.strip()).strip()


def split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    matches = list(heading_pattern.finditer(text))
    if not matches:
        return text.strip(), []

    intro = text[: matches[0].start()].strip()
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(2).strip(), text[start:end].strip()))
    return intro, sections


def canonical_section_name(heading: str) -> str | None:
    lowered = heading.strip().lower()
    for canonical, patterns in SECTION_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            return canonical
    return None


def extract_checklists(text: str) -> list[str]:
    tasks: list[str] = []
    for raw in text.splitlines():
        match = re.match(r"[-*]\s+\[(?: |x|X)\]\s+(.+)", raw.strip())
        if match:
            tasks.append(match.group(1).strip())
    return tasks


def extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for raw in text.splitlines():
        match = re.match(r"(?:[-*]|\d+\.)\s+(.+)", raw.strip())
        if match:
            bullets.append(match.group(1).strip())
    return bullets


def first_paragraph(text: str) -> str:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return parts[0] if parts else ""


def collect_points(text: str) -> list[str]:
    points = extract_bullets(text)
    if points:
        return points
    paragraph = first_paragraph(text)
    return [paragraph] if paragraph else []


def build_workflow_hint(*, title: str, body: str, packet: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    normalized = f"{title}\n{body}".lower()

    if len(packet.get("suggestedTasks") or []) >= 3:
        reasons.append("multiple_implementation_steps")
    if len(packet.get("scope") or []) >= 2:
        reasons.append("multi_scope_change")
    if packet.get("dataContracts"):
        reasons.append("has_data_or_api_contracts")
    if packet.get("constraints"):
        reasons.append("has_constraints_or_risks")

    for pattern, reason in SUBSTANTIAL_SIGNAL_PATTERNS:
        if re.search(pattern, normalized) and reason not in reasons:
            reasons.append(reason)

    substantial = len(reasons) >= 2 or "has_data_or_api_contracts" in reasons
    source_type = str((packet.get("source") or {}).get("type", "")).strip()
    if source_type == "github_issue":
        recommended_tracking = "continue_in_existing_issue"
    elif substantial:
        recommended_tracking = "create_or_use_github_issue"
    else:
        recommended_tracking = "lightweight_task_or_chat_note"

    return {
        "substantialWork": substantial,
        "recommendedTracking": recommended_tracking,
        "recommendedBrief": "execution_brief" if substantial else "lightweight_checklist",
        "reasons": reasons,
    }


def parse_prd_text(*, title: str, body: str, source: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_markdown(body)
    intro, raw_sections = split_sections(normalized)
    buckets: dict[str, list[str]] = {
        "objective": [],
        "scope": [],
        "constraints": [],
        "acceptanceCriteria": [],
        "dataContracts": [],
        "testing": [],
        "openQuestions": [],
        "tasks": [],
    }
    all_checklists = extract_checklists(normalized)

    if intro:
        buckets["objective"].extend(collect_points(intro))

    for heading, section_body in raw_sections:
        canonical = canonical_section_name(heading)
        if not canonical:
            continue
        if canonical == "tasks":
            buckets["tasks"].extend(extract_checklists(section_body) or collect_points(section_body))
            continue
        buckets[canonical].extend(collect_points(section_body))

    for task in all_checklists:
        if task not in buckets["tasks"]:
            buckets["tasks"].append(task)

    gaps: list[str] = []
    if not buckets["objective"]:
        gaps.append("missing_objective")
    if not buckets["acceptanceCriteria"]:
        gaps.append("missing_acceptance_criteria")
    if not buckets["tasks"]:
        gaps.append("missing_suggested_tasks")
    if not buckets["testing"]:
        gaps.append("missing_testing_notes")

    confidence = "high"
    if len(gaps) >= 3:
        confidence = "low"
    elif gaps:
        confidence = "medium"

    packet = {
        "prdPacketVersion": PACKET_VERSION,
        "source": source,
        "title": title,
        "objective": buckets["objective"],
        "scope": buckets["scope"],
        "constraints": buckets["constraints"],
        "acceptanceCriteria": buckets["acceptanceCriteria"],
        "dataContracts": buckets["dataContracts"],
        "testing": buckets["testing"],
        "openQuestions": buckets["openQuestions"],
        "suggestedTasks": buckets["tasks"],
        "gaps": gaps,
        "confidence": confidence,
    }
    packet["workflowHint"] = build_workflow_hint(title=title, body=normalized, packet=packet)
    return packet


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [f"# PRD Packet: {packet['title']}", ""]
    workflow_hint = packet.get("workflowHint") or {}
    if workflow_hint:
        lines.extend(
            [
                "## Workflow Hint",
                "",
                f"- Substantial work: `{workflow_hint.get('substantialWork', False)}`",
                f"- Recommended tracking: `{workflow_hint.get('recommendedTracking', '')}`",
                f"- Recommended brief: `{workflow_hint.get('recommendedBrief', '')}`",
                "",
            ]
        )

    sections = [
        ("Objective", packet.get("objective") or []),
        ("Scope", packet.get("scope") or []),
        ("Constraints", packet.get("constraints") or []),
        ("Acceptance Criteria", packet.get("acceptanceCriteria") or []),
        ("Data / Contracts", packet.get("dataContracts") or []),
        ("Testing", packet.get("testing") or []),
        ("Open Questions", packet.get("openQuestions") or []),
        ("Suggested Tasks", packet.get("suggestedTasks") or []),
        ("Gaps", packet.get("gaps") or []),
    ]
    for heading, items in sections:
        if not items:
            continue
        lines.extend([f"## {heading}", ""])
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
