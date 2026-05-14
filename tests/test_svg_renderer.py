# SPDX-License-Identifier: Apache-2.0
"""Tests for SVG rendering from evidence cards."""

from __future__ import annotations

import importlib.util as ilu
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_renderer():
    script_path = REPO_ROOT / "scripts" / "claimbound_render_evidence_card_svg.py"
    spec = ilu.spec_from_file_location("claimbound_render_evidence_card_svg_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grok_card_renders_svg_without_placeholders() -> None:
    renderer = _load_renderer()
    card_path = (
        REPO_ROOT
        / "docs"
        / "evidence_cards"
        / "CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json"
    )

    svg = renderer.render_svg(card_path, REPO_ROOT / "docs" / "assets" / "claimbound_evidence_card.svg")

    assert "{{" not in svg
    assert "..." not in svg
    assert "Grok prompt repo passed source audit" in svg
    assert "PASSED_UNDER_PROTOCOL" in svg
    assert "not independently reproduced" in svg
    assert "GROK_PROMPTS_SOURCE_AUDIT_D001" in svg
    assert "docs/evidence_cards/" in svg
    assert "CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json" in svg
    assert 'width="2000" height="1190"' in svg
    assert "ClaimBound public benchmarks logo" in svg


def test_status_and_reproduction_colors_are_rendered() -> None:
    renderer = _load_renderer()

    noaa_svg = renderer.render_svg(
        REPO_ROOT
        / "docs"
        / "evidence_cards"
        / "CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json"
    )
    nasa_svg = renderer.render_svg(
        REPO_ROOT
        / "docs"
        / "evidence_cards"
        / "CLAIMBOUND-NASA-POWER-D103-2026-04-29.json"
    )
    blocked_svg = renderer.render_svg(
        REPO_ROOT
        / "docs"
        / "evidence_cards"
        / "CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.json"
    )

    assert 'fill="url(#redGrad)"' in noaa_svg
    assert 'fill="url(#yellowGrad)"' in nasa_svg
    assert "OUTCOME REPRODUCED; BYTE DRIFT" in nasa_svg
    assert 'fill="url(#amberGrad)"' in blocked_svg
