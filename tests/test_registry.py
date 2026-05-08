# SPDX-License-Identifier: Apache-2.0
"""Tests for the ClaimBound public evidence registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from claimbound_public_benchmarks.registry import load_registry, validate_registry

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_committed_registry_matches_cards_and_statistics() -> None:
    registry_path = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
    registry = load_registry(registry_path)

    assert validate_registry(registry, REPO_ROOT) == []


def test_registry_validator_detects_statistics_drift() -> None:
    registry_path = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
    registry = load_registry(registry_path)
    registry["statistics"]["by_result_status"]["PASSED_UNDER_PROTOCOL"] = 999

    violations = validate_registry(registry, REPO_ROOT)

    assert "statistics must match registry card metadata" in violations


def test_registry_cli_reports_violations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    registry_path = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
    registry = load_registry(registry_path)
    registry["cards"][0]["result_status"] = "WRONG_STATUS"
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")

    import importlib.util as ilu

    script_path = REPO_ROOT / "scripts" / "claimbound_validate_registry.py"
    spec = ilu.spec_from_file_location("claimbound_validate_registry_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(sys, "argv", ["claimbound_validate_registry.py", str(path)])

    assert module.main() == 1
    captured = capsys.readouterr()
    assert "registry field mismatch: result_status" in captured.err
