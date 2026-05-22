# SPDX-License-Identifier: Apache-2.0
"""Validation helpers for ClaimBound R&D family ledgers."""

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
    "parent_claim",
    "non_overlap_boundary",
    "claim_scope",
    "track_budget",
    "stop_rules",
    "claim_list",
    "tracks",
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

    return proof_counts


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
        return True
    return False
