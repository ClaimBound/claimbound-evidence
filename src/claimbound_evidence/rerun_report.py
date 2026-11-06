# SPDX-License-Identifier: Apache-2.0
"""Independent rerun report: reproduction status and source-byte drift.

The helper only compares hashes the operator supplies. It never reads, edits
or reclassifies an evidence card or its original claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPRODUCTION_STATUSES = (
    "NOT_RERUN",
    "REPRODUCED",
    "PARTIALLY_REPRODUCED",
    "NOT_REPRODUCED",
    "SOURCE_DRIFT",
    "BLOCKED_SOURCE",
)
DRIFT_CLASSES = ("NO_DRIFT", "SOURCE_BYTE_DRIFT", "MISSING_ORIGINAL", "MISSING_RERUN")


def classify_hashes(original: dict[str, str], rerun: dict[str, str]) -> dict[str, Any]:
    """Compare name -> sha256 maps and classify per-file and overall drift."""

    files: dict[str, str] = {}
    for name in sorted(set(original) | set(rerun)):
        if name not in rerun:
            files[name] = "MISSING_RERUN"
        elif name not in original:
            files[name] = "MISSING_ORIGINAL"
        elif original[name] == rerun[name]:
            files[name] = "NO_DRIFT"
        else:
            files[name] = "SOURCE_BYTE_DRIFT"
    drifted = any(v != "NO_DRIFT" for v in files.values())
    return {"drift": "SOURCE_BYTE_DRIFT" if drifted else "NO_DRIFT", "files": files}


def suggest_status(outcome_matches: bool | None, drift: str, blocked: bool = False) -> str:
    """Suggest a vocabulary status from operator-supplied facts."""

    if blocked:
        return "BLOCKED_SOURCE"
    if outcome_matches is None:
        return "NOT_RERUN"
    if not outcome_matches:
        return "NOT_REPRODUCED"
    return "SOURCE_DRIFT" if drift != "NO_DRIFT" else "REPRODUCED"


def build_report(
    original: dict[str, str],
    rerun: dict[str, str],
    *,
    outcome_matches: bool | None,
    blocked: bool = False,
    operator_note: str = "",
) -> dict[str, Any]:
    drift = classify_hashes(original, rerun)
    report: dict[str, Any] = {
        "reproduction_status": suggest_status(outcome_matches, drift["drift"], blocked),
        "source_drift": drift,
        "card_modified": False,
    }
    if operator_note:
        report["operator_note"] = operator_note
    errors = validate_report(report)
    if errors:
        raise ValueError("; ".join(errors))
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    """Validate the optional rerun-report fields; absent fields are fine."""

    errors: list[str] = []
    status = report.get("reproduction_status")
    if status is not None and status not in REPRODUCTION_STATUSES:
        errors.append(f"reproduction_status must be one of {list(REPRODUCTION_STATUSES)}")
    drift = report.get("source_drift")
    if drift is not None:
        if not isinstance(drift, dict) or drift.get("drift") not in ("NO_DRIFT", "SOURCE_BYTE_DRIFT"):
            errors.append("source_drift.drift must be NO_DRIFT or SOURCE_BYTE_DRIFT")
        else:
            for name, cls in (drift.get("files") or {}).items():
                if cls not in DRIFT_CLASSES:
                    errors.append(f"source_drift.files[{name}] invalid: {cls}")
    note = report.get("operator_note")
    if note is not None and not isinstance(note, str):
        errors.append("operator_note must be a string")
    return errors


def load_hash_map(path: Path) -> dict[str, str]:
    """Load a JSON {name: sha256} map or a `sha256  name` text file."""

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
            raise ValueError(f"{path}: expected a JSON object of name -> sha256")
        return dict(data)
    result: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            result[parts[1].strip().lstrip("*")] = parts[0]
    return result
