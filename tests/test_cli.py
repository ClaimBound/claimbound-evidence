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
