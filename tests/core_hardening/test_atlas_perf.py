# SPDX-License-Identifier: Apache-2.0
"""CPU-time budget for the atlas on a large registry, run with ``-m perf``."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from protocolith.core.atlas import build_atlas_result

pytestmark = pytest.mark.perf

COUNT = 10_000
BUDGET_SECONDS = 3.0
STATUSES = ("PASSED_UNDER_PROTOCOL", "NEGATIVE_RESULT_UNDER_PROTOCOL", "BLOCKED_SOURCE", "INSUFFICIENT_COVERAGE")


def test_atlas_of_10000_cards_stays_fast(tmp_path: Path) -> None:
    folder = tmp_path / "cards"
    folder.mkdir()
    for n in range(COUNT):
        card = {
            "evidence_id": f"PLITH-PERF-2026-01-{n:06d}",
            "protocol_id": f"PERF_{n % 40}",
            "result_status": STATUSES[n % 4],
            "domain": f"domain-{n % 25}",
            "reproduction_level": "not independently reproduced",
            "claim_boundary": "Only the stated gate on the stated source and period. " * 3,
            "created_at": f"2026-{n % 12 + 1:02d}-{n % 28 + 1:02d}",
            "known_limitations": ["Single operator.", "No ranking is claimed."],
            "official_source_name": "Demo source",
            "official_source_url": f"https://example.org/{n}",
        }
        (folder / f"c{n}.json").write_text(json.dumps(card), encoding="utf-8")
    start = time.process_time()
    result = build_atlas_result(cards=[folder])
    elapsed = time.process_time() - start
    assert result.total == COUNT and result.skipped == 0
    assert elapsed < BUDGET_SECONDS, f"{elapsed:.2f} s CPU for {COUNT} cards"
    assert len(result.html) < 15_000_000
