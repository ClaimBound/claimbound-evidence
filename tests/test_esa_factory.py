from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_esa_factory_showcase import SUMMARY_PATH, _collect  # noqa: E402
from esa_factory_data import expected_protocol_ids, load_matrix  # noqa: E402


@pytest.mark.parametrize(
    ("issue_number", "first_protocol", "last_protocol"),
    [
        (133, "ESA-SMOS-01-D401", "ESA-GAIA-20-D500"),
        (134, "ESA-JUICE-01-D501", "ESA-CHEOPS-20-D600"),
        (135, "ESA-ARIEL-01-D601", "ESA-CLUSTER-20-D700"),
    ],
)
def test_esa_factory_matrix(
    issue_number: int, first_protocol: str, last_protocol: str
) -> None:
    matrix, payload = load_matrix(issue_number)

    assert len(matrix["cards"]) == 100
    assert matrix["cards"][0]["protocol_id"] == first_protocol
    assert matrix["cards"][-1]["protocol_id"] == last_protocol
    assert {row["protocol_id"] for row in matrix["cards"]} == expected_protocol_ids(
        issue_number
    )
    assert json.loads(payload) == matrix


def test_esa_factory_showcase_matches_batch_reports_and_registry() -> None:
    committed = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert _collect() == committed
    assert committed["card_count"] == 500
    assert committed["mission_count"] == 25
    assert len(committed["insufficient_coverage"]) == committed["result_counts"].get(
        "INSUFFICIENT_COVERAGE", 0
    )
