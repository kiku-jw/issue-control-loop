"""Choose the right amount of process for a piece of work."""

from __future__ import annotations

import re
from typing import Any

from .prd import extract_bullets, extract_checklists, normalize_markdown


SUBSTANTIAL_SIGNAL_PATTERNS = (
    (r"\bmigration\b|\bschema\b|\bdata contract\b|\bapi contract\b", "touches_schema_or_contracts"),
    (r"\bdependency\b|\bnpm install\b|\bpip install\b|\bpackage\b", "adds_or_changes_dependencies"),
    (r"\brollout\b|\bdeploy\b|\bwebhook\b|\brate limit\b|\bbackground worker\b|\bqueue\b", "has_rollout_or_backend_risk"),
    (r"\bauth\b|\bpermission\b|\brls\b|\bstorage\b|\bupload\b", "touches_security_or_access_boundaries"),
    (r"\bcross-repo\b|\bcross repo\b|\bmultiple repos\b|\bmonorepo\b", "crosses_repo_boundaries"),
)
HIGH_RISK_SIGNAL_PATTERNS = (
    (r"\bauth\b|\bjwt\b|\boauth\b|\bpassword\b|\breset\b|\bsession\b", "auth_or_session_surface"),
    (r"\bsecret\b|\bapi key\b|\btoken\b|\bcredential\b", "secret_or_token_handling"),
    (r"\bpayment\b|\bstripe\b|\bbilling\b", "payment_surface"),
    (r"\bdelete account\b|\bgdpr\b|\bexport data\b", "legal_or_data_retention_surface"),
    (r"\bproduction\b|\blive users\b|\bincident\b", "production_impact"),
)
PUBLIC_SIGNAL_PATTERNS = (
    (r"\bworkflow\b|\bpipeline\b|\bplaybook\b|\bpattern\b", "reusable_workflow"),
    (r"\bhow to\b|\bguide\b|\btutorial\b|\bdiary\b|\bpost\b|\bblog\b", "explicit_public_format"),
    (r"\brepo\b|\bgithub\b|\btool\b|\bcli\b|\btemplate\b", "public_artifact_anchor"),
    (r"\blesson\b|\blearned\b|\bmistake\b|\bpivot\b|\btradeoff\b", "story_has_lessons"),
    (r"\brepeatable\b|\breusable\b|\bfor others\b|\bpublic\b", "useful_beyond_one_session"),
)
PRIVATE_SIGNAL_PATTERNS = (
    (r"/Users/|/home/|C:\\\\", "local_paths"),
    (r"\bprivate repo\b|\bsettings/actions/security\b", "private_repo_reference"),
    (r"\btopic id\b|\bmessageid\b|\bmessage id\b|\bgroup id\b", "internal_chat_jargon"),
    (r"\bhetzner\b|\bauth-profiles\.json\b", "internal_infra_details"),
    (r"\bsecret\b|\bapi key\b|\btoken\b|\bcredential\b", "sensitive_secret_language"),
)
COUNCIL_SIGNAL_PATTERNS = (
    (r"\btradeoff\b|\bfork\b|\bvs\b|\bversus\b", "explicit_tradeoff"),
    (r"\bwhich\b|\bchoose\b|\bdecision\b|\bshould we\b", "decision_needed"),
    (r"\barchitecture\b|\bprovider\b|\bmodel\b|\borchestration\b", "architecture_choice"),
    (r"\bnon-obvious\b|\bunclear\b|\brisk\b|\bcontradiction\b", "needs_independent_review"),
)
DURABILITY_SIGNAL_PATTERNS = (
    (r"\bremember\b|\bsave\b|\blater\b|\bbacklog\b|\bissue\b", "durable_tracking_requested"),
    (r"\bworkflow\b|\bprocess\b|\bplaybook\b|\btemplate\b", "reusable_reference"),
    (r"\bprd\b|\bspec\b|\bacceptance criteria\b", "structured_execution_input"),
)


def count_pattern_hits(text: str, patterns: tuple[tuple[str, str], ...]) -> list[str]:
    return [reason for pattern, reason in patterns if re.search(pattern, text)]


def classify_work(*, title: str, body: str, source: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_markdown(body)
    lowered = f"{title}\n{normalized}".lower()

    bullets = extract_bullets(normalized)
    checklists = extract_checklists(normalized)
    substantial_reasons = count_pattern_hits(lowered, SUBSTANTIAL_SIGNAL_PATTERNS)
    high_risk_reasons = count_pattern_hits(lowered, HIGH_RISK_SIGNAL_PATTERNS)
    public_reasons = count_pattern_hits(lowered, PUBLIC_SIGNAL_PATTERNS)
    private_reasons = count_pattern_hits(lowered, PRIVATE_SIGNAL_PATTERNS)
    council_reasons = count_pattern_hits(lowered, COUNCIL_SIGNAL_PATTERNS)
    durable_reasons = count_pattern_hits(lowered, DURABILITY_SIGNAL_PATTERNS)

    if len(checklists) >= 3 and "multiple_steps" not in substantial_reasons:
        substantial_reasons.append("multiple_steps")
    if len(bullets) >= 5 and "longer_spec_or_plan" not in substantial_reasons:
        substantial_reasons.append("longer_spec_or_plan")
    if len(normalized.splitlines()) >= 18 and "longer_spec_or_plan" not in substantial_reasons:
        substantial_reasons.append("longer_spec_or_plan")

    work_size = "substantial" if len(substantial_reasons) >= 2 or bool(high_risk_reasons) else "tiny"
    high_risk = bool(high_risk_reasons)
    durable = work_size == "substantial" or bool(durable_reasons) or bool(public_reasons)

    if work_size == "substantial":
        tracking = "github-issue"
    elif durable:
        tracking = "local-note"
    else:
        tracking = "chat"

    if work_size == "substantial":
        brief_mode = "execution-brief"
    elif checklists or len(bullets) >= 2:
        brief_mode = "lightweight-checklist"
    else:
        brief_mode = "none"

    if high_risk and council_reasons:
        review_mode = "council"
    elif work_size == "substantial" or durable:
        review_mode = "operator-review"
    else:
        review_mode = "none"

    if public_reasons and not private_reasons:
        publication_potential = "public-draft"
    elif public_reasons or (durable and "reusable_reference" in durable_reasons):
        publication_potential = "private-diary"
    else:
        publication_potential = "none"

    if publication_potential == "public-draft" and work_size == "tiny" and len(public_reasons) < 3 and not checklists:
        publication_potential = "private-diary"

    why = substantial_reasons + high_risk_reasons + public_reasons + durable_reasons + council_reasons
    if private_reasons:
        why.append("contains_private_or_internal_details")

    return {
        "title": title,
        "source": source or {"type": "text"},
        "workSize": work_size,
        "tracking": tracking,
        "briefMode": brief_mode,
        "reviewMode": review_mode,
        "publicationPotential": publication_potential,
        "highRisk": high_risk,
        "why": why[:6],
        "privateSignals": private_reasons,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Work Shaping: {result['title']}",
        "",
        f"- Work size: `{result['workSize']}`",
        f"- Tracking: `{result['tracking']}`",
        f"- Brief mode: `{result['briefMode']}`",
        f"- Review mode: `{result['reviewMode']}`",
        f"- Publication potential: `{result['publicationPotential']}`",
        f"- High risk: `{result['highRisk']}`",
    ]
    if result.get("why"):
        lines.extend(["", "## Why", ""])
        for reason in result["why"]:
            lines.append(f"- {reason}")
    return "\n".join(lines).strip() + "\n"
