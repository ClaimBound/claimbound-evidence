# SPDX-License-Identifier: Apache-2.0
"""Tests for ClaimBound protocol v3 tree overlays."""

from __future__ import annotations

from claimbound_public_benchmarks.tree_overlay import validate_tree_overlay


def _valid_tree() -> dict[str, object]:
    return {
        "tree_id": "EXAMPLE_D001_TREE",
        "protocol_version": "claimbound-tree-v3",
        "tree_status": "ACTIVE",
        "root_family_id": "EXAMPLE_D001_FAMILY",
        "claim_nodes": [
            {
                "claim_id": "EXAMPLE_D001-C001",
                "claim_kind": "iron_claim",
                "status": "FROZEN",
                "claim_text": "The frozen source boundary is identified before outcome scoring.",
                "evidence_required": ["source URL", "access date", "rights note"],
                "acceptance_gate": "Source boundary is recorded before the proof track runs.",
                "forbidden_inference": ["source availability alone is not proof of the empirical claim"],
                "proof_surface_hash": "NOT_COMPUTED_UNTIL_FREEZE",
            },
            {
                "claim_id": "EXAMPLE_D001-C002",
                "claim_kind": "flow_claim",
                "status": "DRAFT",
                "claim_text": "A later diagnostic track may inspect source coverage without proof status.",
                "evidence_required": ["diagnostic summary", "no-proof boundary"],
                "acceptance_gate": "Diagnostic output is recorded only as candidate or blocker evidence.",
                "forbidden_inference": ["diagnostic output is not a deployment or production claim"],
            },
        ],
        "track_nodes": [
            {
                "track_id": "EXAMPLE_D001-T001",
                "mode": "source_audit",
                "claim_ids": ["EXAMPLE_D001-C001"],
                "dependencies": [],
                "branch_status": "runnable",
            }
        ],
        "tombstones": [],
        "badge_counts": {
            "iron_claims": 1,
            "flow_claims": 1,
            "tombstones": 0,
        },
        "branch_block_rules": [
            "A stopped branch must publish a tombstone before descendants can be treated as runnable."
        ],
    }


def test_valid_tree_overlay_passes() -> None:
    assert validate_tree_overlay(_valid_tree()) == []


def test_tree_overlay_rejects_v2_protocol_string() -> None:
    tree = _valid_tree()
    tree["protocol_version"] = "claimbound-rnd-family-v2"

    violations = validate_tree_overlay(tree)

    assert any("claimbound-tree-v3" in violation for violation in violations)


def test_tree_overlay_rejects_bad_badge_counts() -> None:
    tree = _valid_tree()
    tree["badge_counts"] = {"iron_claims": 0, "flow_claims": 1, "tombstones": 0}

    violations = validate_tree_overlay(tree)

    assert any("badge_counts.iron_claims" in violation for violation in violations)


def test_tree_overlay_rejects_unknown_claim_reference() -> None:
    tree = _valid_tree()
    tree["track_nodes"] = [
        {
            "track_id": "EXAMPLE_D001-T001",
            "mode": "source_audit",
            "claim_ids": ["MISSING-C999"],
            "dependencies": [],
            "branch_status": "runnable",
        }
    ]

    violations = validate_tree_overlay(tree)

    assert any("unknown claim_id" in violation for violation in violations)
