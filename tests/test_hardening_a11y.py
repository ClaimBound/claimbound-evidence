# SPDX-License-Identifier: Apache-2.0
"""Tests for non-fatal card hardening warnings and SVG accessibility lint."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.card_svg_styles import (
    MIN_TEXT_CONTRAST,
    contrast_ratio,
    text_color_pairs,
)
from claimbound_evidence.evidence_card import validate_evidence_card, warn_evidence_card
from claimbound_evidence.registry import load_registry, validate_registry
from claimbound_evidence.svg_a11y import lint_svg_text

REPO_ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = REPO_ROOT / "docs" / "evidence_cards"
GOOD_CARD = CARDS_DIR / "CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json"


@pytest.fixture()
def good_card() -> dict:
    return json.loads(GOOD_CARD.read_text(encoding="utf-8"))


def test_good_card_has_no_warnings(good_card: dict) -> None:
    assert validate_evidence_card(good_card) == []
    assert warn_evidence_card(good_card) == []


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("sanitized_report_sha256", "ABC123", "SHA-256"),
        ("access_date", "07/05/2026", "access_date"),
        ("created_at", "2026-13-40", "created_at"),
        ("last_verified_date", "yesterday", "last_verified_date"),
        ("claim_boundary", "too short", "claim_boundary"),
        ("known_limitations", ["ok", "  "], "known_limitations"),
        ("official_source_url", "ftp://example.org/x", "official_source_url"),
    ],
)
def test_bad_fixtures_produce_warnings_not_errors(
    good_card: dict, field: str, value: object, fragment: str
) -> None:
    bad = copy.deepcopy(good_card)
    bad[field] = value
    warnings = warn_evidence_card(bad)
    assert any(fragment in item for item in warnings), warnings
    # Hardening checks never add violations that the strict validator lacks.
    assert not any("should" in item for item in validate_evidence_card(good_card))


def test_raw_payload_committed_true_is_a_hard_violation(good_card: dict) -> None:
    bad = copy.deepcopy(good_card)
    bad["raw_payload_committed"] = True
    assert "raw_payload_committed must be false" in validate_evidence_card(bad)


def test_status_enum_and_boundary_presence_are_hard_violations(good_card: dict) -> None:
    bad = copy.deepcopy(good_card)
    bad["result_status"] = "SUPER_PASS"
    bad["claim_boundary"] = ""
    violations = validate_evidence_card(bad)
    assert any(v.startswith("result_status must be one of") for v in violations)
    assert "missing required field: claim_boundary" in violations


def test_registry_collects_warnings_without_failing() -> None:
    registry = load_registry(REPO_ROOT / "docs" / "registry" / "evidence_index.json")
    warnings: list[str] = []
    assert validate_registry(registry, REPO_ROOT, warnings) == []
    assert isinstance(warnings, list)


def test_registry_duplicate_ids_still_detected() -> None:
    registry = load_registry(REPO_ROOT / "docs" / "registry" / "evidence_index.json")
    registry["cards"] = registry["cards"][:2]
    registry["cards"][1] = dict(registry["cards"][0])
    registry["card_count"] = 2
    violations = validate_registry(registry, REPO_ROOT)
    assert any("duplicate evidence_id" in v for v in violations)


def test_contrast_function_known_values() -> None:
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0)
    assert contrast_ratio("#777777", "#ffffff") < MIN_TEXT_CONTRAST


def test_renderer_palette_meets_text_contrast() -> None:
    pairs = text_color_pairs()
    assert pairs
    low = [p for p in pairs if p[3] < MIN_TEXT_CONTRAST]
    assert low == []


def test_rendered_card_is_a11y_clean() -> None:
    svg = render_svg(GOOD_CARD)
    assert 'role="img"' in svg
    assert 'aria-labelledby="cb-title cb-desc"' in svg
    assert "<title" in svg and "<desc" in svg
    assert lint_svg_text(svg) == []


def test_lint_flags_bad_svg_fixtures() -> None:
    bare = '<svg xmlns="http://www.w3.org/2000/svg"><text fill="#ffffff">x</text></svg>'
    findings = lint_svg_text(bare)
    assert 'root <svg> lacks role="img"' in findings
    assert "root <svg> lacks aria-labelledby" in findings

    low_contrast = (
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d">'
        '<title id="t">t</title><desc id="d">d</desc>'
        '<defs><linearGradient id="yGrad"><stop offset="0" stop-color="#fbbf24"/>'
        "</linearGradient></defs>"
        '<rect width="10" height="10" fill="url(#yGrad)"/>'
        '<text fill="#ffffff">x</text></svg>'
    )
    assert lint_svg_text(low_contrast) == [f"text contrast below {MIN_TEXT_CONTRAST}:1"]
    assert lint_svg_text("<svg") == ["svg is not well-formed XML"]
