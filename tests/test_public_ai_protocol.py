# SPDX-License-Identifier: Apache-2.0
"""Tests for the public AI claim metadata validator."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from claimbound_evidence import public_ai_protocol as p

SCHEMA = Path(__file__).resolve().parents[1] / "specs" / "public_ai_claim_metadata.schema.json"
H = "a" * 64


def _good() -> dict[str, Any]:
    return {
        "schema_version": p.SCHEMA_VERSION,
        "protocol_id": "EXAMPLE_AI001",
        "source_url": "https://example.org/docs/model",
        "source_name": "Example model documentation",
        "source_kind": "model_card",
        "access_date": "2026-01-02",
        "capture_method": "http_fetch",
        "content_sha256": H,
        "model": {
            "provider": "Example Org",
            "model_name": "example-1",
            "model_version": "NOT_STATED",
            "api_metadata_source": "not_stated",
        },
        "prompt_sha256": "NOT_APPLICABLE",
        "transcript_sha256": H,
        "raw_prompt_committed": False,
        "raw_transcript_committed": False,
        "screenshot_only": False,
        "claim_class": "source_audit",
        "claim_boundary": "The source states the listed fields on the access date; nothing else is claimed.",
        "forbidden_implications": list(p.REQUIRED_FORBIDDEN_IMPLICATIONS),
        "stop_rule_triggered": "none",
        "audit_outcome": "recorded",
    }


def test_valid_metadata_passes() -> None:
    assert p.validate_public_ai_claim_metadata(_good()) == []


def test_schema_and_validator_agree() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]
    assert tuple(schema["required"]) == p.REQUIRED_FIELDS
    assert tuple(props["source_kind"]["enum"]) == p.SOURCE_KINDS
    assert tuple(props["capture_method"]["enum"]) == p.CAPTURE_METHODS
    assert tuple(props["claim_class"]["enum"]) == p.CLAIM_CLASSES
    assert tuple(props["stop_rule_triggered"]["enum"]) == p.HALT_CONDITIONS
    assert tuple(props["audit_outcome"]["enum"]) == p.AUDIT_OUTCOMES
    assert tuple(props["model"]["properties"]["api_metadata_source"]["enum"]) == p.API_METADATA_SOURCES
    assert tuple(props["model"]["required"]) == p.MODEL_FIELDS
    contains = {c["contains"]["const"] for c in props["forbidden_implications"]["allOf"]}
    assert contains == set(p.REQUIRED_FORBIDDEN_IMPLICATIONS)


@pytest.mark.parametrize("field", p.REQUIRED_FIELDS)
def test_missing_required_field(field: str) -> None:
    data = _good()
    del data[field]
    assert any(field in e for e in p.validate_public_ai_claim_metadata(data))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_url", "file:///etc/passwd"),
        ("source_url", "ftp://example.org/x"),
        ("protocol_id", "bad id"),
        ("access_date", "2026/01/02"),
        ("content_sha256", "NOT_APPLICABLE"),
        ("content_sha256", "ABC"),
        ("prompt_sha256", "not-a-hash"),
        ("transcript_sha256", "A" * 64),
        ("raw_prompt_committed", True),
        ("raw_transcript_committed", True),
        ("stop_rule_triggered", "whatever"),
        ("audit_outcome", "PASSED_UNDER_PROTOCOL"),
        ("source_kind", "rumor"),
        ("schema_version", "v0"),
    ],
)
def test_bad_values_rejected(field: str, value: object) -> None:
    data = _good()
    data[field] = value
    assert p.validate_public_ai_claim_metadata(data)


def test_forbidden_implications_must_be_complete() -> None:
    data = _good()
    data["forbidden_implications"] = ["model_safety"]
    errors = p.validate_public_ai_claim_metadata(data)
    assert any("benchmark_superiority" in e for e in errors)


def test_model_fields_required() -> None:
    data = _good()
    del data["model"]["model_version"]
    assert any("model_version" in e for e in p.validate_public_ai_claim_metadata(data))


def test_overclaim_boundary_rejected() -> None:
    data = _good()
    data["claim_boundary"] = "The model is safe and outperforms rivals."
    assert any("overclaim" in e for e in p.validate_public_ai_claim_metadata(data))


def test_screenshot_only_limits() -> None:
    data = copy.deepcopy(_good())
    data["screenshot_only"] = True
    data["capture_method"] = "screenshot"
    errors = p.validate_public_ai_claim_metadata(data)
    assert any("screenshot_sha256" in e for e in errors)
    assert any("source_audit_screenshot_limited" in e for e in errors)
    data["claim_class"] = "source_audit_screenshot_limited"
    data["screenshot_sha256"] = H
    data["stop_rule_triggered"] = "screenshot_only_coverage"
    data["audit_outcome"] = "INSUFFICIENT_COVERAGE"
    assert p.validate_public_ai_claim_metadata(data) == []


def test_screenshot_class_requires_flag() -> None:
    data = _good()
    data["claim_class"] = "source_audit_screenshot_limited"
    assert p.validate_public_ai_claim_metadata(data)


def test_triggered_stop_rule_cannot_be_recorded() -> None:
    data = _good()
    data["stop_rule_triggered"] = "rights_unclear"
    assert p.validate_public_ai_claim_metadata(data)
    data["audit_outcome"] = "BLOCKED_SOURCE"
    assert p.validate_public_ai_claim_metadata(data) == []


def test_non_mapping_rejected() -> None:
    assert p.validate_public_ai_claim_metadata([])  # type: ignore[arg-type]
