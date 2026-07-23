from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from claimbound_gate_locator import build_locator_matrix, locate_gate


def test_gate_locator_finds_verbatim_topic_specific_evidence() -> None:
    text = (
        "The official survey reports forest loss across the monitored region during 2024. "
        "Forest loss estimates may be uncertain where cloud coverage is incomplete."
    )
    time = locate_gate(text, "forest loss", "time-boundary")
    negative = locate_gate(text, "forest loss", "negative-evidence")
    assert time.locator == "The official survey reports forest loss across the monitored region during 2024."
    assert negative.locator == "Forest loss estimates may be uncertain where cloud coverage is incomplete."


def test_gate_locator_rejects_unrelated_generic_footer() -> None:
    decision = locate_gate(
        "This official agency published data in 2024. Contact the department.",
        "coral bleaching",
        "time-boundary",
    )
    assert decision.locator is None


def test_locator_matrix_is_sparse_and_gate_aware() -> None:
    claims = [
        {"domain_code": "DOM001", "topic_index": 1, "topic": "forest loss", "gate": "time-boundary"},
        {"domain_code": "DOM001", "topic_index": 1, "topic": "forest loss", "gate": "comparator"},
    ]
    matrix = build_locator_matrix(
        {"DOM001-T01": "Forest loss was measured during 2024 for the monitored region."},
        claims,
    )
    assert "time-boundary" in matrix["DOM001-T01"]
    assert "comparator" not in matrix["DOM001-T01"]


def test_numerator_denominator_requires_all_facets() -> None:
    weak = locate_gate("The forest loss rate was 7%.", "forest loss", "numerator-denominator")
    complete = locate_gate(
        "The number of forest loss events was 70 out of a total population of 1,000 sites, a rate of 7%; missing sites were excluded and percentages were rounded.",
        "forest loss",
        "numerator-denominator",
    )
    assert weak.locator is None
    assert complete.locator is not None
