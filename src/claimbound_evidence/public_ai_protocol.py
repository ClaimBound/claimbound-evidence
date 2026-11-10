# SPDX-License-Identifier: Apache-2.0
"""Stdlib validator for public AI claim source-audit metadata.

Mirrors ``specs/public_ai_claim_metadata.schema.json`` and
``docs/PUBLIC_AI_CLAIM_PROTOCOL.md``. It checks metadata shape and honesty
constraints only; it never assigns a result status.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "claimbound-public-ai-claim-v1"

SOURCE_KINDS = (
    "official_docs",
    "model_card",
    "api_reference",
    "system_card",
    "repository",
    "blog_post",
    "screenshot_only",
    "other",
)
CAPTURE_METHODS = ("http_fetch", "manual_copy", "archive_snapshot", "screenshot")
CLAIM_CLASSES = ("source_audit", "source_audit_screenshot_limited")
API_METADATA_SOURCES = ("documented", "observed", "not_stated")
HALT_CONDITIONS = (
    "none",
    "source_blocked",
    "rights_unclear",
    "hash_missing",
    "model_identity_unverifiable",
    "screenshot_only_coverage",
    "protocol_changed_after_outcome",
)
AUDIT_OUTCOMES = ("recorded", "BLOCKED_SOURCE", "INSUFFICIENT_COVERAGE")
REQUIRED_FORBIDDEN_IMPLICATIONS = (
    "model_safety",
    "model_quality",
    "runtime_behavior",
    "benchmark_superiority",
)
REQUIRED_FIELDS = (
    "schema_version",
    "protocol_id",
    "source_url",
    "source_name",
    "source_kind",
    "access_date",
    "capture_method",
    "content_sha256",
    "model",
    "prompt_sha256",
    "transcript_sha256",
    "raw_prompt_committed",
    "raw_transcript_committed",
    "screenshot_only",
    "claim_class",
    "claim_boundary",
    "forbidden_implications",
    "stop_rule_triggered",
    "audit_outcome",
)
MODEL_FIELDS = ("provider", "model_name", "model_version", "api_metadata_source")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PROTOCOL_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{2,63}$")
# Value used when a prompt or transcript legitimately does not exist.
NOT_APPLICABLE = "NOT_APPLICABLE"
_OVERCLAIM_RE = re.compile(
    r"\b(is safe|are safe|safer than|outperforms?|superior|state[- ]of[- ]the[- ]art|"
    r"best model|guarantees?|certified|production[- ]ready)\b",
    re.IGNORECASE,
)


def _hash_or_na(value: object, name: str, errors: list[str]) -> None:
    if value == NOT_APPLICABLE:
        return
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        errors.append(f"{name} must be a lowercase sha256 hex digest or {NOT_APPLICABLE}")


def validate_public_ai_claim_metadata(data: Mapping[str, Any]) -> list[str]:
    """Return a list of problems; an empty list means the metadata conforms."""

    errors: list[str] = []
    if not isinstance(data, Mapping):
        return ["metadata must be an object"]

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors

    if data["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data["protocol_id"], str) or not _PROTOCOL_ID_RE.match(data["protocol_id"]):
        errors.append("protocol_id must match [A-Z0-9][A-Z0-9_]{2,63}")

    parsed = urlparse(data["source_url"]) if isinstance(data["source_url"], str) else None
    if parsed is None or parsed.scheme not in ("http", "https") or not parsed.netloc:
        errors.append("source_url must be an http or https URL")
    for name in ("source_name", "claim_boundary"):
        if not isinstance(data[name], str) or not data[name].strip():
            errors.append(f"{name} must be a non-empty string")
    if data["source_kind"] not in SOURCE_KINDS:
        errors.append(f"source_kind must be one of {list(SOURCE_KINDS)}")
    if not isinstance(data["access_date"], str) or not _DATE_RE.match(data["access_date"]):
        errors.append("access_date must be YYYY-MM-DD")
    if data["capture_method"] not in CAPTURE_METHODS:
        errors.append(f"capture_method must be one of {list(CAPTURE_METHODS)}")

    _hash_or_na(data["prompt_sha256"], "prompt_sha256", errors)
    _hash_or_na(data["transcript_sha256"], "transcript_sha256", errors)
    if not isinstance(data["content_sha256"], str) or not _SHA256_RE.match(data["content_sha256"]):
        errors.append("content_sha256 must be a lowercase sha256 hex digest")

    for name in ("raw_prompt_committed", "raw_transcript_committed"):
        if data[name] is not False:
            errors.append(f"{name} must be false (store hashes, never raw text)")

    model = data["model"]
    if not isinstance(model, Mapping):
        errors.append("model must be an object")
    else:
        for field in MODEL_FIELDS:
            if not isinstance(model.get(field), str) or not model[field].strip():
                errors.append(f"model.{field} must be a non-empty string (use NOT_STATED if unknown)")
        if model.get("api_metadata_source") not in API_METADATA_SOURCES:
            errors.append(f"model.api_metadata_source must be one of {list(API_METADATA_SOURCES)}")
        endpoint = model.get("api_endpoint")
        if endpoint is not None and not isinstance(endpoint, str):
            errors.append("model.api_endpoint must be a string when present")

    if not isinstance(data["screenshot_only"], bool):
        errors.append("screenshot_only must be a boolean")
    if data["claim_class"] not in CLAIM_CLASSES:
        errors.append(f"claim_class must be one of {list(CLAIM_CLASSES)}")
    shot_only = data["screenshot_only"] is True or data["capture_method"] == "screenshot" or data["source_kind"] == "screenshot_only"
    if shot_only:
        if data["claim_class"] != "source_audit_screenshot_limited":
            errors.append("screenshot-only sources must use claim_class source_audit_screenshot_limited")
        if data["screenshot_only"] is not True:
            errors.append("screenshot capture requires screenshot_only to be true")
        if not isinstance(data.get("screenshot_sha256"), str) or not _SHA256_RE.match(data.get("screenshot_sha256", "")):
            errors.append("screenshot-only sources require screenshot_sha256")
        if data["audit_outcome"] == "recorded" and data["stop_rule_triggered"] == "none":
            errors.append("screenshot-only sources must trigger stop rule screenshot_only_coverage or end as INSUFFICIENT_COVERAGE")
    elif data["claim_class"] == "source_audit_screenshot_limited":
        errors.append("claim_class source_audit_screenshot_limited requires screenshot_only")

    forbidden = data["forbidden_implications"]
    if not isinstance(forbidden, list):
        errors.append("forbidden_implications must be a list")
    else:
        missing = [item for item in REQUIRED_FORBIDDEN_IMPLICATIONS if item not in forbidden]
        if missing:
            errors.append(f"forbidden_implications must include: {missing}")

    if data["stop_rule_triggered"] not in HALT_CONDITIONS:
        errors.append(f"stop_rule_triggered must be one of {list(HALT_CONDITIONS)}")
    if data["audit_outcome"] not in AUDIT_OUTCOMES:
        errors.append(f"audit_outcome must be one of {list(AUDIT_OUTCOMES)}")
    if data["stop_rule_triggered"] not in ("none",) and data["audit_outcome"] == "recorded" and not shot_only:
        errors.append("a triggered stop rule cannot end with audit_outcome recorded")

    if isinstance(data["claim_boundary"], str) and _OVERCLAIM_RE.search(data["claim_boundary"]):
        errors.append("claim_boundary contains an overclaim phrase (safety, quality, superiority or certification)")
    return errors
