# SPDX-License-Identifier: Apache-2.0
"""Tests for ClaimBound R&D family ledgers."""

from __future__ import annotations

from claimbound_evidence.family_ledger import (
    validate_family_ledger,
    validate_frontier_ledger,
)


def _valid_ledger() -> dict[str, object]:
    return {
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
            "dependencies": [],
            "writes_artifacts": [],
        },
        {
            "track_id": "EXAMPLE_D001-T002",
            "mode": "proof",
            "hypothesis_family": "same_branch",
            "claim_ids": ["EXAMPLE_D001-C001"],
            "dependencies": ["EXAMPLE_D001-T001"],
            "writes_artifacts": [],
        },
        {
            "track_id": "EXAMPLE_D001-T003",
            "mode": "proof",
            "hypothesis_family": "same_branch",
            "claim_ids": ["EXAMPLE_D001-C001"],
            "dependencies": ["EXAMPLE_D001-T002"],
            "writes_artifacts": [],
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
            "dependencies": [],
            "writes_artifacts": [],
        }
    ]

    violations = validate_family_ledger(ledger)

    assert any("unknown claim_id" in violation for violation in violations)


def test_valid_frontier_ledger_passes() -> None:
    frontier = {
        "protocol_version": "claimbound-rnd-family-v2",
        "families": [
            {
                "family_id": "EXAMPLE_D001_FAMILY",
                "family_type": "feature_signal_family",
                "status": "alive",
                "current_frontier": ["EXAMPLE_D001-T002"],
                "blocked_claim_flags": ["deployment_readiness"],
                "consumed_tombstones": ["STOP_OLD_BRANCH"],
                "proof_surface_hashes": ["NOT_COMPUTED_UNTIL_FREEZE"],
            }
        ],
        "tombstones": [
            {
                "family_id": "OLD_BRANCH",
                "decision": "STOP_OLD_BRANCH",
                "poisoned_proof_surface_hashes": [
                    "0" * 64,
                ],
                "blocked_future_work": ["reuse_old_surface_as_success"],
                "non_overlap_requirements": ["new source or target surface"],
            }
        ],
    }

    assert validate_frontier_ledger(frontier) == []


def test_frontier_rejects_missing_consumed_tombstone() -> None:
    frontier = {
        "protocol_version": "claimbound-rnd-family-v2",
        "families": [
            {
                "family_id": "EXAMPLE_D001_FAMILY",
                "family_type": "feature_signal_family",
                "status": "alive",
                "current_frontier": ["EXAMPLE_D001-T002"],
                "blocked_claim_flags": ["deployment_readiness"],
                "consumed_tombstones": ["MISSING_STOP"],
                "proof_surface_hashes": ["NOT_COMPUTED_UNTIL_FREEZE"],
            }
        ],
        "tombstones": [],
    }

    violations = validate_frontier_ledger(frontier)

    assert any("unknown tombstone" in violation for violation in violations)
