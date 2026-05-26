# SPDX-License-Identifier: Apache-2.0
"""Validation helpers for ClaimBound v3 tree overlays.

The v3 tree overlay is additive planning/preflight metadata. It does not change
historical evidence cards and it does not create an empirical result by itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROTOCOL_VERSION_V3 = "claimbound-tree-v3"

ALLOWED_TREE_STATUSES = {
    "DRAFT",
    "ACTIVE",
    "CLOSED",
    "SUPERSEDED",
}

ALLOWED_CLAIM_KINDS = {
    "iron_claim",
    "flow_claim",
    "diagnostic_claim",
    "tombstone",
}

ALLOWED_CLAIM_STATUSES = {
    "DRAFT",
    "FROZEN",
    "PASSED",
    "NEGATIVE",
    "BLOCKED",
    "SUPERSEDED",
    "STOPPED",
}

ALLOWED_TRACK_MODES = {
    "source_audit",
    "diagnostic",
    "proof",
    "reproduction",
    "closure",
}

ALLOWED_BRANCH_STATUSES = {
    "runnable",
    "blocked",
    "stopped",
    "closed",
}

REQUIRED_TOP_LEVEL_FIELDS = {
    "tree_id",
    "protocol_version",
    "tree_status",
    "root_family_id",
    "claim_nodes",
    "track_nodes",
    "tombstones",
    "badge_counts",
    "branch_block_rules",
}

REQUIRED_CLAIM_NODE_FIELDS = {
    "claim_id",
    "claim_kind",
    "status",
    "claim_text",
    "evidence_required",
    "acceptance_gate",
    "forbidden_inference",
}

REQUIRED_TRACK_NODE_FIELDS = {
    "track_id",
    "mode",
    "claim_ids",
    "dependencies",
    "branch_status",
}

REQUIRED_TOMBSTONE_FIELDS = {
    "tombstone_id",
    "stopped_family_id",
    "decision",
    "poisoned_proof_surface_hashes",
    "blocked_future_work",
    "non_overlap_requirements",
}

BROAD_CLAIM_FRAGMENTS = {
    "best model",
    "deployment ready",
    "deployment-ready",
    "live operation",
    "production ready",
    "universal edge",
    "universal forecasting edge",
}


def load_tree_overlay(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("tree overlay must be a JSON object")
    return data


def validate_tree_overlay(tree: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    missing = sorted(field for field in REQUIRED_TOP_LEVEL_FIELDS if _is_missing_top_level(tree, field))
    violations.extend(f"missing required field: {field}" for field in missing)

    if tree.get("protocol_version") != PROTOCOL_VERSION_V3:
        violations.append(f"protocol_version must be {PROTOCOL_VERSION_V3!r}")

    if tree.get("tree_status") not in ALLOWED_TREE_STATUSES:
        violations.append(
            "tree_status must be one of: " + ", ".join(sorted(ALLOWED_TREE_STATUSES))
        )

    claim_ids = _validate_claim_nodes(tree.get("claim_nodes"), violations)
    _validate_track_nodes(tree.get("track_nodes"), claim_ids, violations)
    _validate_tombstones(tree.get("tombstones"), violations)
    _validate_badge_counts(
        tree.get("badge_counts"),
        tree.get("claim_nodes"),
        tree.get("tombstones"),
        violations,
    )

    if not isinstance(tree.get("branch_block_rules"), list) or not tree.get("branch_block_rules"):
        violations.append("branch_block_rules must be a non-empty list")

    text = json.dumps(tree, sort_keys=True).lower()
    for fragment in sorted(BROAD_CLAIM_FRAGMENTS):
        if fragment in text:
            violations.append(f"forbidden broad claim fragment: {fragment!r}")

    return violations


def _validate_claim_nodes(value: object, violations: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        violations.append("claim_nodes must be a non-empty list")
        return set()

    claim_ids: set[str] = set()
    for index, item in enumerate(value):
        prefix = f"claim_nodes[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue

        missing = sorted(field for field in REQUIRED_CLAIM_NODE_FIELDS if _is_missing(item.get(field)))
        violations.extend(f"{prefix} missing required field: {field}" for field in missing)

        claim_id = item.get("claim_id")
        if isinstance(claim_id, str):
            if claim_id in claim_ids:
                violations.append(f"duplicate claim_id: {claim_id}")
            claim_ids.add(claim_id)

        if item.get("claim_kind") not in ALLOWED_CLAIM_KINDS:
            violations.append(
                f"{prefix}.claim_kind must be one of: "
                + ", ".join(sorted(ALLOWED_CLAIM_KINDS))
            )

        if item.get("status") not in ALLOWED_CLAIM_STATUSES:
            violations.append(
                f"{prefix}.status must be one of: "
                + ", ".join(sorted(ALLOWED_CLAIM_STATUSES))
            )

        for list_field in ("evidence_required", "forbidden_inference"):
            if not isinstance(item.get(list_field), list) or not item.get(list_field):
                violations.append(f"{prefix}.{list_field} must be a non-empty list")

        if item.get("claim_kind") == "iron_claim" and not _looks_like_sha256_placeholder_or_hash(
            item.get("proof_surface_hash")
        ):
            violations.append(
                f"{prefix}.proof_surface_hash must be SHA-256 hex or NOT_COMPUTED_UNTIL_FREEZE"
            )

    return claim_ids


def _validate_track_nodes(value: object, claim_ids: set[str], violations: list[str]) -> None:
    if not isinstance(value, list) or not value:
        violations.append("track_nodes must be a non-empty list")
        return

    track_ids: set[str] = set()
    for index, item in enumerate(value):
        prefix = f"track_nodes[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue

        missing = sorted(field for field in REQUIRED_TRACK_NODE_FIELDS if _is_missing(item.get(field)))
        violations.extend(f"{prefix} missing required field: {field}" for field in missing)

        track_id = item.get("track_id")
        if isinstance(track_id, str):
            if track_id in track_ids:
                violations.append(f"duplicate track_id: {track_id}")
            track_ids.add(track_id)

        if item.get("mode") not in ALLOWED_TRACK_MODES:
            violations.append(
                f"{prefix}.mode must be one of: "
                + ", ".join(sorted(ALLOWED_TRACK_MODES))
            )

        if item.get("branch_status") not in ALLOWED_BRANCH_STATUSES:
            violations.append(
                f"{prefix}.branch_status must be one of: "
                + ", ".join(sorted(ALLOWED_BRANCH_STATUSES))
            )

        refs = item.get("claim_ids")
        if isinstance(refs, list):
            for claim_id in refs:
                if claim_id not in claim_ids:
                    violations.append(f"{prefix}.claim_ids references unknown claim_id: {claim_id!r}")
        elif refs is not None:
            violations.append(f"{prefix}.claim_ids must be a list")

        if not isinstance(item.get("dependencies"), list):
            violations.append(f"{prefix}.dependencies must be a list")


def _validate_tombstones(value: object, violations: list[str]) -> None:
    if not isinstance(value, list):
        violations.append("tombstones must be a list")
        return

    tombstone_ids: set[str] = set()
    for index, item in enumerate(value):
        prefix = f"tombstones[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue

        missing = sorted(field for field in REQUIRED_TOMBSTONE_FIELDS if _is_missing(item.get(field)))
        violations.extend(f"{prefix} missing required field: {field}" for field in missing)

        tombstone_id = item.get("tombstone_id")
        if isinstance(tombstone_id, str):
            if tombstone_id in tombstone_ids:
                violations.append(f"duplicate tombstone_id: {tombstone_id}")
            tombstone_ids.add(tombstone_id)

        for list_field in (
            "poisoned_proof_surface_hashes",
            "blocked_future_work",
            "non_overlap_requirements",
        ):
            if not isinstance(item.get(list_field), list) or not item.get(list_field):
                violations.append(f"{prefix}.{list_field} must be a non-empty list")

        hashes = item.get("poisoned_proof_surface_hashes")
        if isinstance(hashes, list):
            for proof_hash in hashes:
                if not _looks_like_sha256_placeholder_or_hash(proof_hash):
                    violations.append(f"{prefix}.poisoned_proof_surface_hashes has invalid hash")


def _validate_badge_counts(
    badge_counts: object,
    claim_nodes: object,
    tombstones: object,
    violations: list[str],
) -> None:
    if not isinstance(badge_counts, dict):
        violations.append("badge_counts must be an object")
        return

    for field in ("iron_claims", "flow_claims", "tombstones"):
        value = badge_counts.get(field)
        if not isinstance(value, int) or value < 0:
            violations.append(f"badge_counts.{field} must be a non-negative integer")

    if isinstance(claim_nodes, list):
        iron = sum(1 for item in claim_nodes if isinstance(item, dict) and item.get("claim_kind") == "iron_claim")
        flow = sum(1 for item in claim_nodes if isinstance(item, dict) and item.get("claim_kind") == "flow_claim")
        if badge_counts.get("iron_claims") != iron:
            violations.append("badge_counts.iron_claims must match iron_claim nodes")
        if badge_counts.get("flow_claims") != flow:
            violations.append("badge_counts.flow_claims must match flow_claim nodes")

    if isinstance(tombstones, list) and badge_counts.get("tombstones") != len(tombstones):
        violations.append("badge_counts.tombstones must match tombstone records")


def _is_missing_top_level(tree: dict[str, Any], field: str) -> bool:
    if field not in tree:
        return True
    value = tree.get(field)
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _looks_like_sha256_placeholder_or_hash(value: object) -> bool:
    if value == "NOT_COMPUTED_UNTIL_FREEZE":
        return True
    if not isinstance(value, str):
        return False
    if len(value) != 64:
        return False
    return all(char in "0123456789abcdef" for char in value.lower())


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
        return True
    return False
