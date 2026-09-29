# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from claimbound_evidence.cli import build_parser, main


def test_cli_parser_has_public_workflow_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "new" in help_text
    assert "new-track" in help_text
    assert "demo" in help_text
    assert "run-root" in help_text
    assert "validate-family" in help_text
    assert "validate-frontier" in help_text
    assert "validate-all" in help_text
    assert "doctor" in help_text


def test_validate_all_command_passes_for_committed_cards() -> None:
    assert main(["validate-all"]) == 0


def test_validate_family_accepts_external_absolute_path(tmp_path: Path) -> None:
    ledger = {
        "family_id": "EXAMPLE_D001_FAMILY",
        "protocol_version": "claimbound-rnd-family-v2",
        "family_status": "ACTIVE",
        "family_type": "feature_signal_family",
        "parent_claim": "A narrow family claim.",
        "non_overlap_boundary": "New source family and new label family.",
        "proof_surface": {
            "source_surface": "https://example.org/source",
            "selection_surface": "frozen public sample",
            "label_or_target_surface": "frozen target",
            "candidate_or_method_surface": "fixed method",
            "decision_rule": "fixed gate",
            "target_metric": "fixed metric",
            "acceptance_gates": ["fixed acceptance gate"],
        },
        "proof_surface_hash": "NOT_COMPUTED_UNTIL_FREEZE",
        "allowed_next_tracks": ["diagnostic", "proof", "closure"],
        "blocked_claim_flags": ["deployment_readiness"],
        "context_budget": {"max_context_lines": 80},
        "claim_scope": {
            "allowed": ["source and diagnostic claims under this family"],
            "forbidden": ["deployment claims"],
        },
        "track_budget": {"max_proof_tracks_per_hypothesis": 2},
        "stop_rules": ["stop after repeated proof negatives"],
        "claim_list": [
            {
                "claim_id": "EXAMPLE_D001-C001",
                "claim_class": "diagnostic",
                "status": "FROZEN",
                "claim_text": "Screen candidates without making proof claims.",
                "evidence_required": ["diagnostic summary"],
                "acceptance_gate": "Candidate recorded only as diagnostic.",
                "forbidden_inference": ["diagnostic output is not proof"],
            }
        ],
        "tracks": [
            {
                "track_id": "EXAMPLE_D001-T001",
                "mode": "diagnostic",
                "hypothesis_family": "feature_inventory",
                "claim_ids": ["EXAMPLE_D001-C001"],
                "dependencies": [],
                "writes_artifacts": [],
            }
        ],
    }
    path = tmp_path / "EXAMPLE_D001_FAMILY_LEDGER.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")

    assert main(["validate-family", str(path)]) == 0


def test_new_prints_absolute_paths_when_out_dir_is_outside_repo(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    from claimbound_evidence import cli

    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    out_dir = tmp_path.parent / "outside_claimbound_repo" / "scaffold"

    assert (
        main(
            [
                "new",
                "--source-url",
                "https://example.org/source-docs",
                "--protocol-id",
                "CLI_NEW_OUT_TEST_D001",
                "--domain",
                "public-data",
                "--track-type",
                "source_audit",
                "--execution-mode",
                "MANUAL_NO_AI",
                "--out",
                str(out_dir),
            ]
        )
        == 0
    )

    stdout = capsys.readouterr().out
    assert "docs/protocols/CLI_NEW_OUT_TEST_D001_PREREG_CHARTER.md" in stdout
    assert f"{out_dir.as_posix()}/CLI_NEW_OUT_TEST_D001_PLAYBOOK.md" in stdout


def test_validate_frontier_accepts_external_absolute_path(tmp_path: Path) -> None:
    frontier = {
        "protocol_version": "claimbound-rnd-family-v2",
        "families": [
            {
                "family_id": "EXAMPLE_D001_FAMILY",
                "family_type": "feature_signal_family",
                "status": "alive",
                "current_frontier": ["EXAMPLE_D001-T001"],
                "blocked_claim_flags": ["deployment_readiness"],
                "consumed_tombstones": [],
                "proof_surface_hashes": ["NOT_COMPUTED_UNTIL_FREEZE"],
            }
        ],
        "tombstones": [],
    }
    path = tmp_path / "EXAMPLE_D001_FRONTIER.json"
    path.write_text(json.dumps(frontier), encoding="utf-8")

    assert main(["validate-frontier", str(path)]) == 0


def _card_path() -> Path:
    from claimbound_evidence import cli

    return cli.REPO_ROOT / "docs" / "evidence_cards" / "CLAIMBOUND-NASA-POWER-D103-2026-04-29.json"


def test_version_flag_prints_package_version(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.startswith("claimbound ")


def test_checkout_commands_explain_missing_clone(tmp_path: Path, monkeypatch, capsys) -> None:
    from claimbound_evidence import cli

    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    for argv in (["validate-all"], ["demo", "validate-all"], ["verify", "starter-pack"]):
        assert main(argv) == 2
        err = capsys.readouterr().err
        assert "needs a clone of the repository" in err
        assert "validate-card" in err


def test_doctor_reports_installed_package_mode(tmp_path: Path, monkeypatch, capsys) -> None:
    from claimbound_evidence import cli

    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "mode=installed-package" in out
    assert "ready=yes" in out
    assert "repo_root=" not in out


def test_validate_card_resolves_relative_path_from_cwd_without_clone(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from claimbound_evidence import cli

    card = tmp_path / "card.json"
    card.write_text(_card_path().read_text(encoding="utf-8"), encoding="utf-8")
    fake_root = tmp_path / "site-packages"
    fake_root.mkdir()
    monkeypatch.setattr(cli, "REPO_ROOT", fake_root)
    monkeypatch.chdir(tmp_path)

    assert main(["validate-card", "card.json"]) == 0
    assert "valid_card=" in capsys.readouterr().out


def test_inspect_card_defaults_to_summary_keys(capsys) -> None:
    assert main(["inspect", "card", str(_card_path())]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["result_status"]
    assert "claim_boundary" in out
