# SPDX-License-Identifier: Apache-2.0
"""Validation helpers for ClaimBound R&D family ledgers and frontiers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_FAMILY_STATUSES = {
    "DRAFT",
    "ACTIVE",
    "STOPPED",
    "CLOSED",
    "SUPERSEDED",
}

PROTOCOL_VERSION_V2 = "claimbound-rnd-family-v2"

ALLOWED_FAMILY_TYPES = {
    "source_boundary_family",
    "feature_signal_family",
    "evaluation_family",
    "reproduction_family",
    "systems_performance_family",
    "safety_policy_family",
    "product_decision_family",
    "publication_audit_family",
}

ALLOWED_FRONTIER_STATUSES = {
    "alive",
    "stopped",
    "closed",
}

ALLOWED_CLAIM_CLASSES = {
    "source",
    "availability",
    "causality",
    "diagnostic",
    "predictive",
    "economic",
    "deployment",
    "reproduction",
    "closure",
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

REQUIRED_TOP_LEVEL_FIELDS = {
    "family_id",
    "family_status",
    "family_type",
    "protocol_version",
    "parent_claim",
    "non_overlap_boundary",
    "proof_surface",
    "proof_surface_hash",
    "allowed_next_tracks",
    "blocked_claim_flags",
    "context_budget",
    "claim_scope",
    "track_budget",
    "stop_rules",
    "claim_list",
    "tracks",
}

REQUIRED_PROOF_SURFACE_FIELDS = {
    "source_surface",
    "selection_surface",
    "label_or_target_surface",
    "candidate_or_method_surface",
    "decision_rule",
    "target_metric",
    "acceptance_gates",
}

REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "claim_class",
    "status",
    "claim_text",
    "evidence_required",
    "acceptance_gate",
    "forbidden_inference",
}

REQUIRED_TRACK_FIELDS = {
    "track_id",
    "mode",
    "hypothesis_family",
    "claim_ids",
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


def load_family_ledger(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("family ledger must be a JSON object")
    return data


def load_frontier_ledger(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("frontier ledger must be a JSON object")
    return data


def validate_family_ledger(ledger: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    missing = sorted(field for field in REQUIRED_TOP_LEVEL_FIELDS if _is_missing(ledger.get(field)))
    violations.extend(f"missing required field: {field}" for field in missing)

    family_status = ledger.get("family_status")
    if family_status not in ALLOWED_FAMILY_STATUSES:
        violations.append(
            "family_status must be one of: "
            + ", ".join(sorted(ALLOWED_FAMILY_STATUSES))
        )

    protocol_version = ledger.get("protocol_version")
    if protocol_version != PROTOCOL_VERSION_V2:
        violations.append(f"protocol_version must be {PROTOCOL_VERSION_V2!r}")

    family_type = ledger.get("family_type")
    if family_type not in ALLOWED_FAMILY_TYPES:
        violations.append(
            "family_type must be one of: "
            + ", ".join(sorted(ALLOWED_FAMILY_TYPES))
        )

    proof_surface = ledger.get("proof_surface")
    if isinstance(proof_surface, dict):
        missing_surface = sorted(
            field for field in REQUIRED_PROOF_SURFACE_FIELDS if _is_missing(proof_surface.get(field))
        )
        violations.extend(f"proof_surface missing required field: {field}" for field in missing_surface)
    elif proof_surface is not None:
        violations.append("proof_surface must be an object")

    if not _looks_like_sha256_placeholder_or_hash(ledger.get("proof_surface_hash")):
        violations.append("proof_surface_hash must be SHA-256 hex or NOT_COMPUTED_UNTIL_FREEZE")

    for list_field in ("allowed_next_tracks", "blocked_claim_flags"):
        if not isinstance(ledger.get(list_field), list) or not ledger.get(list_field):
            violations.append(f"{list_field} must be a non-empty list")

    context_budget = ledger.get("context_budget")
    if isinstance(context_budget, dict):
        max_lines = context_budget.get("max_context_lines")
        if not isinstance(max_lines, int) or max_lines < 1:
            violations.append("context_budget.max_context_lines must be a positive integer")
    elif context_budget is not None:
        violations.append("context_budget must be an object")

    claim_scope = ledger.get("claim_scope")
    if isinstance(claim_scope, dict):
        for key in ("allowed", "forbidden"):
            if not isinstance(claim_scope.get(key), list) or not claim_scope.get(key):
                violations.append(f"claim_scope.{key} must be a non-empty list")
    elif claim_scope is not None:
        violations.append("claim_scope must be an object")

    track_budget = ledger.get("track_budget")
    max_proof_tracks = None
    if isinstance(track_budget, dict):
        max_proof_tracks = track_budget.get("max_proof_tracks_per_hypothesis")
        if not isinstance(max_proof_tracks, int) or max_proof_tracks < 1:
            violations.append("track_budget.max_proof_tracks_per_hypothesis must be a positive integer")
    elif track_budget is not None:
        violations.append("track_budget must be an object")

    stop_rules = ledger.get("stop_rules")
    if stop_rules is not None and (not isinstance(stop_rules, list) or not stop_rules):
        violations.append("stop_rules must be a non-empty list")

    claim_ids = _validate_claims(ledger.get("claim_list"), violations)
    proof_counts = _validate_tracks(ledger.get("tracks"), claim_ids, violations)

    if max_proof_tracks is not None:
        for family, count in sorted(proof_counts.items()):
            if count > max_proof_tracks:
                violations.append(
                    f"hypothesis_family {family!r} has {count} proof tracks; "
                    f"budget allows {max_proof_tracks}"
                )

    if family_status in {"STOPPED", "CLOSED"} and _is_missing(ledger.get("closure_decision")):
        violations.append("stopped or closed families must include closure_decision")

    text = json.dumps(ledger, sort_keys=True).lower()
    for fragment in sorted(BROAD_CLAIM_FRAGMENTS):
        if fragment in text:
            violations.append(f"forbidden broad claim fragment: {fragment!r}")

    return violations


def validate_frontier_ledger(frontier: dict[str, Any], base_dir: Path | None = None) -> list[str]:
    violations: list[str] = []

    if frontier.get("protocol_version") != PROTOCOL_VERSION_V2:
        violations.append(f"protocol_version must be {PROTOCOL_VERSION_V2!r}")

    families = frontier.get("families")
    if not isinstance(families, list):
        violations.append("families must be a list")
        families = []

    tombstones = frontier.get("tombstones")
    if not isinstance(tombstones, list):
        violations.append("tombstones must be a list")
        tombstones = []

    tombstone_decisions = set()
    for index, item in enumerate(tombstones):
        prefix = f"tombstones[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue
        for field in (
            "family_id",
            "decision",
        ):
            if _is_missing(item.get(field)):
                violations.append(f"{prefix} missing required field: {field}")

        for list_field in (
            "poisoned_proof_surface_hashes",
            "blocked_future_work",
            "non_overlap_requirements",
        ):
            if list_field not in item:
                violations.append(f"{prefix} missing required field: {list_field}")
            elif not isinstance(item.get(list_field), list) or not item.get(list_field):
                violations.append(f"{prefix}.{list_field} must be a non-empty list")

        decision = item.get("decision")
        if isinstance(decision, str):
            if decision in tombstone_decisions:
                violations.append(f"duplicate tombstone decision: {decision}")
            tombstone_decisions.add(decision)

        hashes = item.get("poisoned_proof_surface_hashes")
        if isinstance(hashes, list):
            for proof_hash in hashes:
                if not _looks_like_sha256_placeholder_or_hash(proof_hash):
                    violations.append(f"{prefix}.poisoned_proof_surface_hashes has invalid hash")

        _validate_optional_frontier_file(item, base_dir, prefix, violations)

    family_ids = set()
    for index, item in enumerate(families):
        prefix = f"families[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue
        for field in (
            "family_id",
            "family_type",
            "status",
        ):
            if _is_missing(item.get(field)):
                violations.append(f"{prefix} missing required field: {field}")

        for list_field in (
            "current_frontier",
            "blocked_claim_flags",
            "consumed_tombstones",
            "proof_surface_hashes",
        ):
            if list_field not in item:
                violations.append(f"{prefix} missing required field: {list_field}")

        family_id = item.get("family_id")
        if isinstance(family_id, str):
            if family_id in family_ids:
                violations.append(f"duplicate family_id: {family_id}")
            family_ids.add(family_id)

        if item.get("family_type") not in ALLOWED_FAMILY_TYPES:
            violations.append(
                f"{prefix}.family_type must be one of: "
                + ", ".join(sorted(ALLOWED_FAMILY_TYPES))
            )

        if item.get("status") not in ALLOWED_FRONTIER_STATUSES:
            violations.append(
                f"{prefix}.status must be one of: "
                + ", ".join(sorted(ALLOWED_FRONTIER_STATUSES))
            )

        for list_field in (
            "current_frontier",
            "blocked_claim_flags",
            "consumed_tombstones",
            "proof_surface_hashes",
        ):
            if not isinstance(item.get(list_field), list):
                violations.append(f"{prefix}.{list_field} must be a list")

        for consumed in item.get("consumed_tombstones", []):
            if consumed not in tombstone_decisions:
                violations.append(f"{prefix}.consumed_tombstones references unknown tombstone: {consumed!r}")

        for proof_hash in item.get("proof_surface_hashes", []):
            if not _looks_like_sha256_placeholder_or_hash(proof_hash):
                violations.append(f"{prefix}.proof_surface_hashes has invalid hash")

        _validate_optional_frontier_file(item, base_dir, prefix, violations)

    text = json.dumps(frontier, sort_keys=True).lower()
    for fragment in sorted(BROAD_CLAIM_FRAGMENTS):
        if fragment in text:
            violations.append(f"forbidden broad claim fragment: {fragment!r}")

    return violations


def _validate_claims(value: object, violations: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        violations.append("claim_list must be a non-empty list")
        return set()

    claim_ids: set[str] = set()
    for index, item in enumerate(value):
        prefix = f"claim_list[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue

        missing = sorted(field for field in REQUIRED_CLAIM_FIELDS if _is_missing(item.get(field)))
        violations.extend(f"{prefix} missing required field: {field}" for field in missing)

        claim_id = item.get("claim_id")
        if isinstance(claim_id, str):
            if claim_id in claim_ids:
                violations.append(f"duplicate claim_id: {claim_id}")
            claim_ids.add(claim_id)

        if item.get("claim_class") not in ALLOWED_CLAIM_CLASSES:
            violations.append(
                f"{prefix}.claim_class must be one of: "
                + ", ".join(sorted(ALLOWED_CLAIM_CLASSES))
            )

        if item.get("status") not in ALLOWED_CLAIM_STATUSES:
            violations.append(
                f"{prefix}.status must be one of: "
                + ", ".join(sorted(ALLOWED_CLAIM_STATUSES))
            )

        for list_field in ("evidence_required", "forbidden_inference"):
            if not isinstance(item.get(list_field), list) or not item.get(list_field):
                violations.append(f"{prefix}.{list_field} must be a non-empty list")

    return claim_ids


def _validate_tracks(
    value: object, claim_ids: set[str], violations: list[str]
) -> dict[str, int]:
    if not isinstance(value, list) or not value:
        violations.append("tracks must be a non-empty list")
        return {}

    track_ids: set[str] = set()
    proof_counts: dict[str, int] = {}

    for index, item in enumerate(value):
        prefix = f"tracks[{index}]"
        if not isinstance(item, dict):
            violations.append(f"{prefix} must be an object")
            continue

        missing = sorted(field for field in REQUIRED_TRACK_FIELDS if _is_missing(item.get(field)))
        violations.extend(f"{prefix} missing required field: {field}" for field in missing)

        track_id = item.get("track_id")
        if isinstance(track_id, str):
            if track_id in track_ids:
                violations.append(f"duplicate track_id: {track_id}")
            track_ids.add(track_id)

        mode = item.get("mode")
        if mode not in ALLOWED_TRACK_MODES:
            violations.append(
                f"{prefix}.mode must be one of: "
                + ", ".join(sorted(ALLOWED_TRACK_MODES))
            )

        family = item.get("hypothesis_family")
        if mode == "proof" and isinstance(family, str):
            proof_counts[family] = proof_counts.get(family, 0) + 1

        refs = item.get("claim_ids")
        if isinstance(refs, list):
            for claim_id in refs:
                if claim_id not in claim_ids:
                    violations.append(f"{prefix}.claim_ids references unknown claim_id: {claim_id!r}")
        elif refs is not None:
            violations.append(f"{prefix}.claim_ids must be a list")

        for list_field in ("dependencies", "writes_artifacts"):
            if not isinstance(item.get(list_field), list):
                violations.append(f"{prefix}.{list_field} must be a list")

    return proof_counts


def _validate_optional_frontier_file(
    item: dict[str, Any],
    base_dir: Path | None,
    prefix: str,
    violations: list[str],
) -> None:
    path_value = item.get("context_capsule_path") or item.get("path")
    if base_dir is None or not isinstance(path_value, str) or not path_value:
        return

    path = base_dir / path_value
    if not path.exists():
        violations.append(f"{prefix} references missing file: {path_value}")
        return

    try:
        detail = load_frontier_ledger(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        violations.append(f"{prefix} referenced file is not valid JSON object: {path_value}: {exc}")
        return

    if detail.get("protocol_version") != PROTOCOL_VERSION_V2:
        violations.append(f"{prefix} referenced file has wrong protocol_version: {path_value}")

    if "family_id" in item and "family_id" in detail and detail["family_id"] != item["family_id"]:
        violations.append(f"{prefix} referenced file has mismatched family_id: {path_value}")

    if "decision" in item and "decision" in detail and detail["decision"] != item["decision"]:
        violations.append(f"{prefix} referenced file has mismatched decision: {path_value}")


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
