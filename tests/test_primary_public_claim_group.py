from __future__ import annotations

import json
from pathlib import Path

from claimbound_evidence.evidence_card import validate_evidence_card


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = sorted(ROOT.glob("artifacts/cb7k_dom*_primary_claims.json"))


def test_each_primary_group_has_ten_distinct_claims_and_existing_slots() -> None:
    assert len(MANIFESTS) >= 2
    for path in MANIFESTS:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        rows = manifest["records"]
        assert len(rows) == 10
        assert len({row["protocol_id"] for row in rows}) == 10
        assert len({row["public_claim_text"] for row in rows}) == 10
        assert len({row["public_claim_verbatim_quote"] for row in rows}) == 10
        assert manifest["raw_payload_committed"] is False
        assert "retrospective" in manifest["review_design"]


def test_primary_group_cards_match_manifest_and_validate() -> None:
    checked = 0
    for manifest_path in MANIFESTS:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in manifest["records"]:
            matches = list((ROOT / "docs/evidence_cards").glob(f"CLAIMBOUND-{row['protocol_id']}-*.json"))
            assert len(matches) == 1
            card = json.loads(matches[0].read_text(encoding="utf-8"))
            assert card["public_claim_text"] == row["public_claim_text"]
            assert card["public_claim_verbatim_quote"] == row["public_claim_verbatim_quote"]
            assert card["public_claim_source_url"] == manifest["source_url"]
            assert card["public_claim_source_sha256"] == manifest["source_sha256"]
            assert card["result_status"] == "PASSED_UNDER_PROTOCOL"
            assert validate_evidence_card(card) == []
            checked += 1
    assert checked == 10 * len(MANIFESTS)
