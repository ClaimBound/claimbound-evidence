# SPDX-License-Identifier: Apache-2.0
"""Validation helpers for the ClaimBound public evidence registry."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from claimbound_public_benchmarks.evidence_card import validate_evidence_card


ENTRY_CARD_FIELDS = {
    "domain",
    "evidence_id",
    "official_source_name",
    "record_type",
    "reproduction_level",
    "result_status",
    "sanitized_report_path",
    "registry_sequence",
    "operator",
    "last_verified_date",
    "verification_count",
    "verification_level",
}


def load_registry(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("registry must be a JSON object")
    return data


def validate_registry(registry: dict[str, Any], repo_root: Path) -> list[str]:
    violations: list[str] = []
    cards = registry.get("cards")
    if not isinstance(cards, list):
        return ["registry.cards must be a list"]

    if registry.get("card_count") != len(cards):
        violations.append("card_count must match number of registry cards")

    seen_sequences: set[int] = set()
    seen_ids: set[str] = set()
    entries_for_stats: list[dict[str, Any]] = []

    for index, entry in enumerate(cards, start=1):
        if not isinstance(entry, dict):
            violations.append(f"registry card #{index} must be an object")
            continue

        evidence_id = str(entry.get("evidence_id", f"#{index}"))
        if evidence_id in seen_ids:
            violations.append(f"duplicate evidence_id in registry: {evidence_id}")
        seen_ids.add(evidence_id)

        sequence = entry.get("registry_sequence")
        if not isinstance(sequence, int) or sequence < 1:
            violations.append(f"{evidence_id}: registry_sequence must be positive integer")
        elif sequence in seen_sequences:
            violations.append(f"{evidence_id}: duplicate registry_sequence {sequence}")
        else:
            seen_sequences.add(sequence)

        path_value = entry.get("path")
        if not isinstance(path_value, str) or not path_value:
            violations.append(f"{evidence_id}: missing registry path")
            continue

        card_path = repo_root / path_value
        if not card_path.is_file():
            violations.append(f"{evidence_id}: card path does not exist: {path_value}")
            continue

        card = json.loads(card_path.read_text(encoding="utf-8"))
        card_violations = validate_evidence_card(card)
        violations.extend(f"{evidence_id}: {item}" for item in card_violations)

        for field in sorted(ENTRY_CARD_FIELDS):
            if entry.get(field) != card.get(field):
                violations.append(f"{evidence_id}: registry field mismatch: {field}")

        svg_url = entry.get("svg_url")
        if isinstance(svg_url, str) and svg_url:
            svg_path = _github_blob_url_to_repo_path(svg_url)
            if svg_path is not None and not (repo_root / svg_path).is_file():
                violations.append(f"{evidence_id}: svg_url path does not exist: {svg_path}")

        entries_for_stats.append(entry)

    if seen_sequences and seen_sequences != set(range(1, len(cards) + 1)):
        violations.append("registry_sequence values must be contiguous from 1")

    expected_statistics = _compute_statistics(entries_for_stats)
    if registry.get("statistics") != expected_statistics:
        violations.append("statistics must match registry card metadata")

    return violations


def _compute_statistics(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "by_domain": _count(entries, "domain"),
        "by_record_type": _count(entries, "record_type"),
        "by_result_status": _count(entries, "result_status"),
        "by_source": _count(entries, "official_source_name"),
    }


def _count(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(str(entry.get(field, "")) for entry in entries)
    counter.pop("", None)
    return dict(sorted(counter.items()))


def _github_blob_url_to_repo_path(url: str) -> str | None:
    marker = "/blob/main/"
    if marker not in url:
        return None
    return url.split(marker, 1)[1]
