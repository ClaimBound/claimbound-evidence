# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from claimbound_public_benchmarks.cli import build_parser, main


def test_cli_parser_has_public_workflow_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "new" in help_text
    assert "new-track" in help_text
    assert "demo" in help_text
    assert "run-root" in help_text
    assert "validate-family" in help_text
    assert "validate-all" in help_text


def test_validate_all_command_passes_for_committed_cards() -> None:
    assert main(["validate-all"]) == 0


def test_validate_family_accepts_external_absolute_path(tmp_path: Path) -> None:
    ledger = {
        "family_id": "EXAMPLE_D001_FAMILY",
        "family_status": "ACTIVE",
        "parent_claim": "A narrow family claim.",
        "non_overlap_boundary": "New source family and new label family.",
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
            }
        ],
    }
    path = tmp_path / "EXAMPLE_D001_FAMILY_LEDGER.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")

    assert main(["validate-family", str(path)]) == 0
