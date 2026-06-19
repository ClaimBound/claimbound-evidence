# SPDX-License-Identifier: Apache-2.0
"""Tests for ClaimBound evidence-card validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from claimbound_evidence.evidence_card import validate_evidence_card

REPO_ROOT = Path(__file__).resolve().parents[1]


def _valid_card() -> dict[str, object]:
    return {
        "evidence_id": "CLAIMBOUND-EXAMPLE-001",
        "registry_sequence": 1,
        "record_type": "evidence_result",
        "protocol_id": "EXAMPLE_D001",
        "protocol_version": "0.1.0",
        "domain": "example-public-source",
        "claim_type": "signal",
        "execution_mode": "MANUAL_NO_AI",
        "result_status": "NEGATIVE_RESULT_UNDER_PROTOCOL",
        "claim_boundary": "Example D-001 did not pass the frozen gate.",
        "official_source_name": "Example official source",
        "official_source_url": "https://example.org/source",
        "access_date": "2026-05-01",
        "source_rights_note": "Official public source; raw payloads are not committed.",
        "raw_payload_committed": False,
        "raw_payload_manifest": "external SHA-256 manifest",
        "sanitized_report_path": "artifacts/example_summary.json",
        "sanitized_report_sha256": "0" * 64,
        "git_commit": "0" * 40,
        "runner_command": "manual audit checklist",
        "operator": "maintainer",
        "created_at": "2026-05-01",
        "last_verified_date": "2026-05-01",
        "verification_count": 1,
        "verification_level": "SINGLE_OPERATOR",
        "reproduction_level": "not independently reproduced",
        "ai_assistance": "not used",
        "manual_review": "source boundary and claim boundary reviewed",
        "known_limitations": ["Example card for validation tests."],
    }


def test_valid_evidence_card_passes() -> None:
    assert validate_evidence_card(_valid_card()) == []


def test_committed_evidence_cards_validate_and_are_indexed() -> None:
    card_dir = REPO_ROOT / "docs" / "evidence_cards"
    registry_path = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    indexed_paths = {entry["path"] for entry in registry["cards"]}

    cards = sorted(card_dir.glob("CLAIMBOUND-*.json"))
    assert cards
    assert registry["card_count"] == len(cards)

    for path in cards:
        card = json.loads(path.read_text(encoding="utf-8"))
        assert validate_evidence_card(card) == []
        rel = path.relative_to(REPO_ROOT).as_posix()
        assert rel in indexed_paths
        assert card["raw_payload_committed"] is False


def test_evidence_card_requires_execution_mode() -> None:
    card = _valid_card()
    card.pop("execution_mode")

    violations = validate_evidence_card(card)

    assert "missing required field: execution_mode" in violations


def test_evidence_card_requires_record_type() -> None:
    card = _valid_card()
    card.pop("record_type")

    violations = validate_evidence_card(card)

    assert "missing required field: record_type" in violations


def test_evidence_card_requires_registry_sequence() -> None:
    card = _valid_card()
    card["registry_sequence"] = 0

    violations = validate_evidence_card(card)

    assert "registry_sequence must be a positive integer" in violations


def test_evidence_card_requires_valid_verification_level() -> None:
    card = _valid_card()
    card["verification_level"] = "POPULAR_VOTE"

    violations = validate_evidence_card(card)

    assert "verification_level must be one of" in " ".join(violations)


def test_evidence_card_rejects_raw_payload_committed() -> None:
    card = _valid_card()
    card["raw_payload_committed"] = True

    violations = validate_evidence_card(card)

    assert "raw_payload_committed must be false" in violations


def test_evidence_card_rejects_drift_in_result_status() -> None:
    card = _valid_card()
    card["result_status"] = "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT"
    card["reproduction_level"] = "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT"

    violations = validate_evidence_card(card)

    assert any("result_status must not be REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT" in item for item in violations)


def test_evidence_card_requires_valid_reproduction_level() -> None:
    card = _valid_card()
    card["reproduction_level"] = "maybe reproduced"

    violations = validate_evidence_card(card)

    assert "reproduction_level must be one of" in " ".join(violations)


def test_evidence_card_cli_reports_violations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    card = _valid_card()
    card["execution_mode"] = "BAD_MODE"
    path = tmp_path / "card.json"
    path.write_text(json.dumps(card), encoding="utf-8")

    import importlib.util as ilu

    script_path = REPO_ROOT / "scripts" / "claimbound_validate_evidence_card.py"
    spec = ilu.spec_from_file_location("claimbound_validate_evidence_card_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(sys, "argv", ["claimbound_validate_evidence_card.py", str(path)])

    assert module.main() == 1
    captured = capsys.readouterr()
    assert "execution_mode must be one of" in captured.err
