"""Classify issue-backed work into digest buckets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .control_schema import extract_worker_meta, merge_ops_meta


ALLOWED_BUILD_KINDS = {"Task", "Feature", "Bug", "Research"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
ACTIVE_WORKER_STATES = {"claiming", "claimed"}


@dataclass
class ProjectItem:
    item_id: str
    issue_repo: str
    issue_number: int
    issue_url: str
    title: str
    status: str
    approval: str
    destination: str
    kind: str
    priority: str
    area: str = ""
    source: str = ""


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def lease_is_stale(worker_meta: dict[str, Any] | None, *, now: datetime) -> bool:
    if not worker_meta:
        return False
    state = str(worker_meta.get("state", "")).strip()
    if state not in ACTIVE_WORKER_STATES:
        return False
    expires = parse_iso8601(str(worker_meta.get("leaseExpiresAt", "")).strip())
    return bool(expires and expires <= now)


def needs_human_decision(meta: dict[str, Any]) -> bool:
    return bool(meta.get("needsHumanDecision")) or str(meta.get("state", "")).strip().lower() in {
        "awaiting_review",
        "paused",
    }


def waiting_on_operator(meta: dict[str, Any]) -> bool:
    state = str(meta.get("state", "")).strip().lower()
    owner = str(meta.get("owner", "")).strip().lower()
    blocked_on = str(meta.get("blockedOn", "")).strip().lower()
    return owner in {"nick", "operator"} or "nick" in blocked_on or needs_human_decision(meta) or state in {
        "awaiting_review",
        "paused",
    }


def build_reason(item: ProjectItem, *, ops_meta: dict[str, Any], worker_meta: dict[str, Any] | None) -> str:
    state = str(ops_meta.get("state", "")).strip().lower()
    if state == "awaiting_review":
        return "awaiting operator review"
    if state == "paused":
        return "paused by operator"
    if state == "blocked":
        return str(ops_meta.get("blockedOn", "")).strip() or "blocked"
    if waiting_on_operator(ops_meta):
        return str(ops_meta.get("blockedOn", "")).strip() or "waiting on operator decision"
    if lease_is_stale(worker_meta, now=utc_now()):
        return "stale worker lease"
    if item.status == "In Progress":
        return "already in progress"
    if item.destination == "Build" and item.approval == "Approved":
        return "approved build work"
    if item.destination in {"Blog", "Public Channel"}:
        return "review queue"
    return "needs manual classification"


def classify_item(
    item: ProjectItem,
    *,
    issue_body: str,
    comments: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    ops_meta = merge_ops_meta(issue_body, comments)
    worker_meta = extract_worker_meta(comments or [])
    stale = lease_is_stale(worker_meta, now=utc_now())
    state = str(ops_meta.get("state", "")).strip().lower()

    if state == "blocked":
        section = "waitingOnOperator" if waiting_on_operator(ops_meta) else "staleOrProblem"
    elif waiting_on_operator(ops_meta):
        section = "waitingOnOperator"
    elif stale:
        section = "staleOrProblem"
    elif item.status == "In Progress":
        section = "inProgress"
    elif item.status == "Done":
        section = "done"
    elif item.destination == "Build" and item.approval == "Approved" and item.kind in ALLOWED_BUILD_KINDS:
        section = "readyToStart"
    elif item.destination in {"Blog", "Public Channel"} or (
        item.destination == "Build" and item.approval in {"Needs Review", "Revise"}
    ):
        section = "reviewQueues"
    else:
        section = "unclassified"

    return {
        "section": section,
        "item": {
            "issueRepo": item.issue_repo,
            "issueNumber": item.issue_number,
            "issueUrl": item.issue_url,
            "title": item.title,
            "status": item.status,
            "approval": item.approval,
            "destination": item.destination,
            "kind": item.kind,
            "priority": item.priority,
            "area": item.area,
            "source": item.source,
        },
        "reason": build_reason(item, ops_meta=ops_meta, worker_meta=worker_meta),
        "opsMeta": ops_meta,
        "workerMeta": worker_meta,
        "flags": {
            "waitingOnOperator": waiting_on_operator(ops_meta),
            "needsHumanDecision": needs_human_decision(ops_meta),
            "staleWorkerLease": stale,
        },
    }


def build_digest(entries: list[dict[str, Any]]) -> dict[str, Any]:
    sections = {
        "waitingOnOperator": [],
        "inProgress": [],
        "readyToStart": [],
        "reviewQueues": [],
        "staleOrProblem": [],
        "unclassified": [],
        "done": [],
    }
    for entry in entries:
        sections[entry["section"]].append(entry)

    for key in sections:
        sections[key].sort(key=lambda entry: (PRIORITY_ORDER.get(entry["item"]["priority"], 99), entry["item"]["issueNumber"]))

    return {
        "summary": {key: len(value) for key, value in sections.items()} | {"scanned": len(entries)},
        "sections": sections,
    }
