# SPDX-License-Identifier: Apache-2.0
"""Tests for ClaimBound R&D family ledgers."""

from __future__ import annotations

from claimbound_public_benchmarks.family_ledger import validate_family_ledger


def _valid_ledger() -> dict[str, object]:
    return {
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


def test_valid_family_ledger_passes() -> None:
    assert validate_family_ledger(_valid_ledger()) == []


def test_family_ledger_limits_repeated_proof_tracks() -> None:
    ledger = _valid_ledger()
    ledger["tracks"] = [
        {
            "track_id": "EXAMPLE_D001-T001",
            "mode": "proof",
            "hypothesis_family": "same_branch",
            "claim_ids": ["EXAMPLE_D001-C001"],
        },
        {
            "track_id": "EXAMPLE_D001-T002",
            "mode": "proof",
            "hypothesis_family": "same_branch",
            "claim_ids": ["EXAMPLE_D001-C001"],
        },
        {
            "track_id": "EXAMPLE_D001-T003",
            "mode": "proof",
            "hypothesis_family": "same_branch",
            "claim_ids": ["EXAMPLE_D001-C001"],
        },
    ]

    violations = validate_family_ledger(ledger)

    assert any("budget allows 2" in violation for violation in violations)


def test_family_ledger_rejects_unknown_claim_reference() -> None:
    ledger = _valid_ledger()
    ledger["tracks"] = [
        {
            "track_id": "EXAMPLE_D001-T001",
            "mode": "diagnostic",
            "hypothesis_family": "feature_inventory",
            "claim_ids": ["MISSING-C999"],
        }
    ]

    violations = validate_family_ledger(ledger)

    assert any("unknown claim_id" in violation for violation in violations)
