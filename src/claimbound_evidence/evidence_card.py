# SPDX-License-Identifier: Apache-2.0
"""Validation helpers for ClaimBound evidence cards."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ALLOWED_EXECUTION_MODES = {
    "MANUAL_NO_AI",
    "AUTOMATED_AI_ASSISTED",
}

ALLOWED_RESULT_STATUSES = {
    "PASSED_UNDER_PROTOCOL",
    "NEGATIVE_RESULT_UNDER_PROTOCOL",
    "BLOCKED_SOURCE",
    "INSUFFICIENT_COVERAGE",
    "SOURCE_DRIFT",
    "REPRODUCED_OUTCOME",
}

ALLOWED_REPRODUCTION_LEVELS = {
    "not independently reproduced",
    "REPRODUCED_OUTCOME",
    "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT",
}

ALLOWED_RECORD_TYPES = {
    "evidence_result",
    "source_audit",
    "protocol_registration",
    "reproduction_attempt",
}

ALLOWED_VERIFICATION_LEVELS = {
    "SINGLE_OPERATOR",
    "SINGLE_OPERATOR_RERUN",
    "INDEPENDENT_RERUN",
    "MULTI_OPERATOR",
    "NOT_EXECUTED",
}

REQUIRED_FIELDS = {
    "evidence_id",
    "registry_sequence",
    "record_type",
    "protocol_id",
    "protocol_version",
    "domain",
    "claim_type",
    "execution_mode",
    "result_status",
    "claim_boundary",
    "official_source_name",
    "official_source_url",
    "access_date",
    "source_rights_note",
    "raw_payload_committed",
    "raw_payload_manifest",
    "sanitized_report_path",
    "sanitized_report_sha256",
    "git_commit",
    "runner_command",
    "operator",
    "created_at",
    "last_verified_date",
    "verification_count",
    "verification_level",
    "reproduction_level",
    "ai_assistance",
    "manual_review",
    "known_limitations",
}

FORECAST_REQUIRED_FIELDS = {
    "forecast_question",
    "answer_timestamp",
    "forecast_deadline",
    "resolution_deadline",
    "model_or_method",
    "resolution_rule",
    "allowed_resolution_sources",
    "scoring_rule",
}

FORBIDDEN_CLAIM_FRAGMENTS = {
    "best model",
    "model is best",
    "broad model superiority",
    "deployment ready",
    "deployment-ready",
    "production ready",
    "universal forecasting edge",
    "universal effect",
    "proves correctness outside",
}

# Cards created before this policy remain readable as historical records.  Every
# card created on or after the cutoff must bind the result to a concrete public
# statement.  This is deliberately date based so a producer cannot opt out by
# choosing an older schema version or record type.
PUBLIC_CLAIM_POLICY_START = date(2026, 7, 26)
PUBLIC_CLAIM_REQUIRED_FIELDS = {
    "public_claim_text",
    "public_claim_verbatim_quote",
    "public_claim_source_url",
    "public_claim_locator",
    "public_claim_captured_at",
    "public_claim_source_sha256",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CANDIDATE_QUESTION_FRAGMENTS = {
    "the public claim about",
    "the published number for",
    "can be traced to one exact public source",
    "does not silently exclude",
}


def load_evidence_card(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evidence card must be a JSON object")
    return data


def validate_evidence_card(card: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    missing = sorted(field for field in REQUIRED_FIELDS if _is_missing(card.get(field)))
    violations.extend(f"missing required field: {field}" for field in missing)

    execution_mode = card.get("execution_mode")
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        violations.append(
            "execution_mode must be one of: "
            + ", ".join(sorted(ALLOWED_EXECUTION_MODES))
        )

    result_status = card.get("result_status")
    if result_status == "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT":
        violations.append(
            "result_status must not be REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT; "
            "set reproduction_level instead and keep result_status as the gate outcome"
        )
    elif result_status not in ALLOWED_RESULT_STATUSES:
        violations.append(
            "result_status must be one of: "
            + ", ".join(sorted(ALLOWED_RESULT_STATUSES))
        )

    reproduction_level = card.get("reproduction_level")
    if reproduction_level not in ALLOWED_REPRODUCTION_LEVELS:
        violations.append(
            "reproduction_level must be one of: "
            + ", ".join(sorted(ALLOWED_REPRODUCTION_LEVELS))
        )

    record_type = card.get("record_type")
    if record_type not in ALLOWED_RECORD_TYPES:
        violations.append(
            "record_type must be one of: "
            + ", ".join(sorted(ALLOWED_RECORD_TYPES))
        )

    if card.get("raw_payload_committed") is not False:
        violations.append("raw_payload_committed must be false")

    registry_sequence = card.get("registry_sequence")
    if not isinstance(registry_sequence, int) or registry_sequence < 1:
        violations.append("registry_sequence must be a positive integer")

    verification_count = card.get("verification_count")
    if not isinstance(verification_count, int) or verification_count < 0:
        violations.append("verification_count must be a non-negative integer")

    verification_level = card.get("verification_level")
    if verification_level not in ALLOWED_VERIFICATION_LEVELS:
        violations.append(
            "verification_level must be one of: "
            + ", ".join(sorted(ALLOWED_VERIFICATION_LEVELS))
        )

    claim_type = str(card.get("claim_type", "")).lower()
    if claim_type == "forecast":
        missing_forecast = sorted(
            field for field in FORECAST_REQUIRED_FIELDS if _is_missing(card.get(field))
        )
        violations.extend(
            f"missing forecast field: {field}" for field in missing_forecast
        )

    if result_status == "PASSED_UNDER_PROTOCOL" and _is_missing(
        card.get("baseline_control_summary")
    ):
        violations.append("positive records must include baseline_control_summary")

    if result_status == "BLOCKED_SOURCE" and _is_missing(card.get("block_reason")):
        violations.append("blocked records must include block_reason")

    if result_status == "SOURCE_DRIFT" and _is_missing(card.get("drift_reason")):
        violations.append("source drift records must include drift_reason")

    text = json.dumps(card, sort_keys=True).lower()
    for fragment in sorted(FORBIDDEN_CLAIM_FRAGMENTS):
        if fragment in text:
            violations.append(f"forbidden broad claim fragment: {fragment!r}")

    mode_text = str(card.get("execution_mode", ""))
    ai_assistance = str(card.get("ai_assistance", "")).lower()
    if "AI_ASSISTED" in mode_text and ai_assistance in {"", "none", "not used"}:
        violations.append("AI-assisted execution modes must describe ai_assistance")

    if mode_text.endswith("_NO_AI") and "used" in ai_assistance and "not used" not in ai_assistance:
        violations.append("NO_AI execution modes must not describe AI use")

    violations.extend(_validate_public_claim_binding(card))

    return violations


def _validate_public_claim_binding(card: dict[str, Any]) -> list[str]:
    """Require a source-bound public statement for every newly created card."""
    created = str(card.get("created_at", ""))[:10]
    try:
        policy_applies = date.fromisoformat(created) >= PUBLIC_CLAIM_POLICY_START
    except ValueError:
        return []  # The ordinary required-field validation handles bad/missing values.
    if not policy_applies:
        return []

    violations: list[str] = []
    missing = sorted(
        field for field in PUBLIC_CLAIM_REQUIRED_FIELDS if _is_missing(card.get(field))
    )
    violations.extend(f"missing public claim field: {field}" for field in missing)
    if missing:
        return violations

    claim = str(card["public_claim_text"]).strip()
    quote = str(card["public_claim_verbatim_quote"]).strip()
    locator = str(card["public_claim_locator"]).strip()
    source_url = str(card["public_claim_source_url"]).strip()
    source_sha256 = str(card["public_claim_source_sha256"]).strip()

    if len(claim) < 20 or claim.endswith("?"):
        violations.append("public_claim_text must be a concrete declarative statement")
    lowered_claim = claim.lower()
    if any(fragment in lowered_claim for fragment in _CANDIDATE_QUESTION_FRAGMENTS):
        violations.append("public_claim_text must not be a generated gate template")
    if len(quote) < 20:
        violations.append("public_claim_verbatim_quote must contain a substantive source excerpt")
    if len(locator) < 8:
        violations.append("public_claim_locator must identify the quote within the source")
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or not parsed.netloc:
        violations.append("public_claim_source_url must be an absolute HTTPS URL")
    if not _SHA256_RE.fullmatch(source_sha256):
        violations.append("public_claim_source_sha256 must be a lowercase SHA-256 digest")
    try:
        captured = date.fromisoformat(str(card["public_claim_captured_at"])[:10])
        if captured > date.fromisoformat(created):
            violations.append("public_claim_captured_at must not be later than created_at")
    except ValueError:
        violations.append("public_claim_captured_at must start with an ISO date")
    return violations


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
        return True
    return False
