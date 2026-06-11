# SPDX-License-Identifier: Apache-2.0
"""Tests for SVG rendering from evidence cards."""

from __future__ import annotations

import re
from pathlib import Path

from claimbound_evidence.card_svg_render import render_svg

REPO_ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = REPO_ROOT / "docs" / "evidence_cards"


def test_grok_card_renders_svg_without_placeholders() -> None:
    card_path = CARDS_DIR / "CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json"
    svg = render_svg(card_path)

    assert "{{" not in svg
    assert "..." not in svg
    assert "Grok prompt repo passed source audit" in svg
    assert "PASSED_UNDER_PROTOCOL" in svg
    assert "not independently reproduced" in svg
    assert "GROK_PROMPTS_SOURCE_AUDIT_D001" in svg
    assert "docs/evidence_cards/" in svg
    assert "CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json" in svg
    assert 'width="2000" height="1190"' in svg
    assert "ClaimBound evidence logo" in svg


def test_status_and_reproduction_colors_are_rendered() -> None:
    noaa_svg = render_svg(CARDS_DIR / "CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json")
    nasa_svg = render_svg(CARDS_DIR / "CLAIMBOUND-NASA-POWER-D103-2026-04-29.json")
    blocked_svg = render_svg(CARDS_DIR / "CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.json")

    assert 'fill="url(#redGrad)"' in noaa_svg
    assert 'fill="url(#yellowGrad)"' in nasa_svg
    assert "OUTCOME REPRODUCED; BYTE DRIFT" in nasa_svg
    assert 'fill="url(#amberGrad)"' in blocked_svg


def test_svg_uses_inline_text_styles_for_github_readme_safety() -> None:
    svg = render_svg(CARDS_DIR / "CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json")

    assert "<style>" not in svg
    assert 'class="claimText"' not in svg
    assert 'fill="#0d1736"' in svg
    assert 'font-size="39"' in svg
    assert "PASSED_UNDER_PROTOCOL" in svg


def test_software_dev_card_claim_sentence_is_gate_pass_not_validator_failure() -> None:
    svg = render_svg(CARDS_DIR / "CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json")
    visible = re.sub(r"<[^>]+>", " ", svg)
    collapsed = " ".join(visible.split())

    assert "required-field regression gate passed for execution_mode enforcement" in collapsed
    assert "validator rejects" not in collapsed.lower()
    assert "validator rejected" not in collapsed.lower()
