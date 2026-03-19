"""Helpers for marker-based GitHub issue state."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


OPS_BODY_MARKER_START = "<!-- issue-control-meta:start -->"
OPS_BODY_MARKER_END = "<!-- issue-control-meta:end -->"
OPS_STATE_MARKER_START = "<!-- issue-control-state:start -->"
OPS_STATE_MARKER_END = "<!-- issue-control-state:end -->"
EXEC_PLAN_MARKER_START = "<!-- issue-exec-plan:start -->"
EXEC_PLAN_MARKER_END = "<!-- issue-exec-plan:end -->"
EXEC_RUN_MARKER_START = "<!-- issue-exec-run:start -->"
EXEC_RUN_MARKER_END = "<!-- issue-exec-run:end -->"
WORKER_MARKER_START = "<!-- issue-build-worker:start -->"
WORKER_MARKER_END = "<!-- issue-build-worker:end -->"
PRD_PACKET_MARKER_START = "<!-- issue-prd-packet:start -->"
PRD_PACKET_MARKER_END = "<!-- issue-prd-packet:end -->"

LEGACY_OPS_BODY_MARKER_START = "<!-- openclaw-ops-meta:start -->"
LEGACY_OPS_BODY_MARKER_END = "<!-- openclaw-ops-meta:end -->"
LEGACY_OPS_STATE_MARKER_START = "<!-- openclaw-ops-state:start -->"
LEGACY_OPS_STATE_MARKER_END = "<!-- openclaw-ops-state:end -->"
LEGACY_EXEC_PLAN_MARKER_START = "<!-- openclaw-exec-plan:start -->"
LEGACY_EXEC_PLAN_MARKER_END = "<!-- openclaw-exec-plan:end -->"
LEGACY_EXEC_RUN_MARKER_START = "<!-- openclaw-executor-run:start -->"
LEGACY_EXEC_RUN_MARKER_END = "<!-- openclaw-executor-run:end -->"
LEGACY_WORKER_MARKER_START = "<!-- openclaw-build-worker:start -->"
LEGACY_WORKER_MARKER_END = "<!-- openclaw-build-worker:end -->"
LEGACY_PRD_PACKET_MARKER_START = "<!-- openclaw-prd-packet:start -->"
LEGACY_PRD_PACKET_MARKER_END = "<!-- openclaw-prd-packet:end -->"


@dataclass
class MarkerDefinition:
    kind: str
    start: str
    end: str
    heading: str
    legacy_pairs: tuple[tuple[str, str], ...] = ()


MARKERS = {
    "ops_state": MarkerDefinition(
        "ops_state",
        OPS_STATE_MARKER_START,
        OPS_STATE_MARKER_END,
        "Control state updated.",
        ((LEGACY_OPS_STATE_MARKER_START, LEGACY_OPS_STATE_MARKER_END),),
    ),
    "exec_plan": MarkerDefinition(
        "exec_plan",
        EXEC_PLAN_MARKER_START,
        EXEC_PLAN_MARKER_END,
        "Execution plan updated.",
        ((LEGACY_EXEC_PLAN_MARKER_START, LEGACY_EXEC_PLAN_MARKER_END),),
    ),
    "exec_run": MarkerDefinition(
        "exec_run",
        EXEC_RUN_MARKER_START,
        EXEC_RUN_MARKER_END,
        "Executor run updated.",
        ((LEGACY_EXEC_RUN_MARKER_START, LEGACY_EXEC_RUN_MARKER_END),),
    ),
}


def extract_marker_json(body: str, *, start: str, end: str) -> dict[str, Any] | None:
    pattern = re.escape(start) + r"\n(.*?)\n" + re.escape(end)
    match = re.search(pattern, body, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def extract_scalar_meta(body: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    field_map = {
        "ops owner": "owner",
        "needs human decision": "needsHumanDecision",
        "blocked on": "blockedOn",
        "state": "state",
        "executor": "executor",
        "target repo": "targetRepo",
        "target subdir": "targetSubdir",
        "last operator action": "lastOperatorAction",
    }
    for raw in body.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        mapped = field_map.get(key.strip().lower())
        if not mapped:
            continue
        cleaned = value.strip()
        if mapped == "needsHumanDecision":
            result[mapped] = cleaned.lower() in {"1", "true", "yes"}
        else:
            result[mapped] = cleaned
    return result


def extract_issue_body_meta(body: str) -> dict[str, Any]:
    meta = extract_marker_json(body, start=OPS_BODY_MARKER_START, end=OPS_BODY_MARKER_END)
    if meta:
        return meta
    meta = extract_marker_json(body, start=LEGACY_OPS_BODY_MARKER_START, end=LEGACY_OPS_BODY_MARKER_END)
    if meta:
        return meta
    return extract_scalar_meta(body)


def find_marker_comment(
    comments: list[dict[str, Any]],
    *,
    start: str,
    end: str,
    legacy_pairs: tuple[tuple[str, str], ...] = (),
) -> dict[str, Any] | None:
    for comment in reversed(comments):
        payload = extract_marker_json(comment.get("body", ""), start=start, end=end)
        if payload is None:
            for legacy_start, legacy_end in legacy_pairs:
                payload = extract_marker_json(comment.get("body", ""), start=legacy_start, end=legacy_end)
                if payload is not None:
                    break
        if payload is None:
            continue
        return {"id": comment.get("id"), "body": comment.get("body", ""), "payload": payload}
    return None


def extract_worker_meta(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    found = find_marker_comment(
        comments,
        start=WORKER_MARKER_START,
        end=WORKER_MARKER_END,
        legacy_pairs=((LEGACY_WORKER_MARKER_START, LEGACY_WORKER_MARKER_END),),
    )
    return found["payload"] if found else None


def extract_control_comments(comments: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    return {
        kind: find_marker_comment(comments, start=marker.start, end=marker.end, legacy_pairs=marker.legacy_pairs)
        for kind, marker in MARKERS.items()
    }


def merge_ops_meta(issue_body: str, comments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    merged = extract_issue_body_meta(issue_body)
    if comments:
        control = extract_control_comments(comments).get("ops_state")
        if control and control.get("payload"):
            for key, value in dict(control["payload"]).items():
                if value in (None, ""):
                    continue
                merged[key] = value
    if str(merged.get("targetRepo", "")).strip() and not str(merged.get("executor", "")).strip():
        merged["executor"] = "codex_local"
    return merged


def render_marker_comment(kind: str, payload: dict[str, Any]) -> str:
    marker = MARKERS[kind]
    lines = [
        marker.start,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        marker.end,
        "",
        marker.heading,
    ]
    return "\n".join(lines).strip() + "\n"
