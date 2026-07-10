# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for the ESA issue #131 local batch runner."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_EXPORT_PATH = REPO_ROOT / "docs" / "esa" / "issue_131_claim_matrix.json"
REGISTRY_PATH = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
CARDS_DIR = REPO_ROOT / "docs" / "evidence_cards"
SUMMARY_PATH = REPO_ROOT / "artifacts" / "esa_issue_131_batch_summary.json"
RUNBOOK_RESULT_PATH = (
    REPO_ROOT / "docs" / "manual_audit" / "ESA-ISSUE-131" / "README.md"
)
USER_AGENT = (
    "Mozilla/5.0 ClaimBound/1.0 "
    "(public ESA source-boundary audit; ClaimBound/claimbound-evidence)"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def write_json(path: Path, data: object) -> bytes:
    payload = (
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def normalize_html(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    for before, after in {
        "\xa0": " ",
        "’": "'",
        "‘": "'",
        "–": "-",
        "—": "-",
        "‑": "-",
        "−": "-",
    }.items():
        text = text.replace(before, after)
    return re.sub(r"\s+", " ", text).strip()


def slug(value: str) -> str:
    value = value.lower().replace("sentinel-", "sentinel_")
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def registry_statistics(
    cards: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    def count(field: str) -> dict[str, int]:
        counter = Counter(str(entry.get(field, "")) for entry in cards)
        counter.pop("", None)
        return dict(sorted(counter.items()))

    return {
        "by_domain": count("domain"),
        "by_record_type": count("record_type"),
        "by_result_status": count("result_status"),
        "by_source": count("official_source_name"),
    }
