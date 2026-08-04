from __future__ import annotations

import json
from pathlib import Path

from claimbound_evidence.evidence_card import validate_evidence_card


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifacts/cb7k_dom001_t01_openai_primary_claims.json"


def test_primary_group_has_ten_distinct_claims_and_existing_slots() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = manifest["records"]
    assert len(rows) == 10
    assert len({row["protocol_id"] for row in rows}) == 10
    assert len({row["public_claim_text"] for row in rows}) == 10
    assert len({row["public_claim_verbatim_quote"] for row in rows}) == 10
    assert manifest["raw_payload_committed"] is False
    assert "retrospective" in manifest["review_design"]


def test_primary_group_cards_match_manifest_and_validate() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cards = {}
    for path in (ROOT / "docs/evidence_cards").glob(
        "CLAIMBOUND-CB7K-DOM001-T01-G*-2026-07-20.json"
    ):
        card = json.loads(path.read_text(encoding="utf-8"))
        cards[card["protocol_id"]] = card
    assert len(cards) == 10
    for row in manifest["records"]:
        card = cards[row["protocol_id"]]
        assert card["public_claim_text"] == row["public_claim_text"]
        assert card["public_claim_verbatim_quote"] == row["public_claim_verbatim_quote"]
        assert card["public_claim_source_url"] == manifest["source_url"]
        assert card["public_claim_source_sha256"] == manifest["source_sha256"]
        assert card["result_status"] == "PASSED_UNDER_PROTOCOL"
        assert validate_evidence_card(card) == []
