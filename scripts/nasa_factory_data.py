# SPDX-License-Identifier: Apache-2.0
"""Load frozen NASA factory matrices exported from issues #147 through #156."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH_ISSUES = tuple(range(147, 157))


def load_matrix(issue_number: int) -> tuple[dict[str, Any], bytes]:
    if issue_number not in BATCH_ISSUES:
        raise ValueError(f"unsupported NASA issue: {issue_number}")
    path = REPO_ROOT / "docs" / "nasa" / f"issue_{issue_number}_claim_matrix.json"
    payload = path.read_bytes()
    matrix = json.loads(payload)
    if not isinstance(matrix, dict) or len(matrix.get("cards", [])) != 50:
        raise ValueError(f"{path}: expected a 50-card matrix")
    return matrix, payload


__all__ = ["BATCH_ISSUES", "load_matrix"]
