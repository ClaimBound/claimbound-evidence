"""Load CB7K card and primary/Wikidata claim rows for the atlas."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .constants import CARDS, MANIFEST, PRIMARY_MANIFESTS, ROOT


def load() -> tuple[dict, list[dict]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    primary_by_protocol: dict[str, tuple[dict, dict, str]] = {}
    for primary_path in PRIMARY_MANIFESTS:
        primary_manifest = json.loads(primary_path.read_text(encoding="utf-8"))
        primary_report_sha = hashlib.sha256(primary_path.read_bytes()).hexdigest()
        for row in primary_manifest["records"]:
            if row["protocol_id"] in primary_by_protocol:
                raise SystemExit(f"ERROR: duplicate primary protocol {row['protocol_id']}")
            primary_by_protocol[row["protocol_id"]] = (row, primary_manifest, primary_report_sha)
    rows: list[dict] = []
    card_paths = sorted(CARDS.glob("CLAIMBOUND-CB7K-*.json"))
    cards_by_protocol = {
        json.loads(path.read_text(encoding="utf-8"))["protocol_id"]: (
            path,
            json.loads(path.read_text(encoding="utf-8")),
        )
        for path in card_paths
    }
    if len(cards_by_protocol) != 7000:
        raise SystemExit(f"ERROR: expected 7000 CB7K cards, got {len(cards_by_protocol)}")
    slots: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    for path, card in cards_by_protocol.values():
        slots[card["protocol_id"].split("-")[1]].append((path, card))
    for values in slots.values():
        values.sort(key=lambda pair: pair[1]["protocol_id"])
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for record in manifest["records"]:
        by_domain[record["domain_code"]].append(record)
    for domain_code in sorted(by_domain):
        for record, (path, card) in zip(by_domain[domain_code], slots[domain_code], strict=True):
            primary_match = primary_by_protocol.get(card["protocol_id"])
            if primary_match:
                rows.append(_primary_row(record, path, card, primary_match))
                continue
            rows.append(_wikidata_row(record, path, card, report_sha))
    if len(rows) != 7000 or len({row["statement_id"] for row in rows}) != 7000:
        raise SystemExit("ERROR: atlas requires 7000 distinct statement IDs")
    return manifest, rows


def _primary_row(
    record: dict,
    path: Path,
    card: dict,
    primary_match: tuple[dict, dict, str],
) -> dict:
    primary, primary_manifest, primary_report_sha = primary_match
    checks = {
        "claim_text": card.get("public_claim_text") == primary["public_claim_text"],
        "verbatim_quote": card.get("public_claim_verbatim_quote")
        == primary["public_claim_verbatim_quote"],
        "source_url": card.get("public_claim_source_url") == primary_manifest["source_url"],
        "locator": card.get("public_claim_locator") == primary["section_locator"],
        "source_sha256": card.get("public_claim_source_sha256")
        == primary_manifest["source_sha256"],
        "report_sha256": card.get("sanitized_report_sha256") == primary_report_sha,
        "passed": card.get("result_status") == "PASSED_UNDER_PROTOCOL",
    }
    if not all(checks.values()):
        raise SystemExit(f"ERROR: card/primary-manifest mismatch {card['evidence_id']}: {checks}")
    return {
        **record,
        **primary,
        "source_kind": "primary",
        "statement_id": f"primary:{card['protocol_id']}",
        "public_claim_source_url": primary_manifest["source_url"],
        "public_claim_source_sha256": primary_manifest["source_sha256"],
        "public_claim_captured_at": primary_manifest["access_date"],
        "wikidata_rank": None,
        "wikidata_reference_count": 0,
        "wikidata_qualifier_count": 0,
        "card": card,
        "card_path": path.relative_to(ROOT).as_posix(),
        "checks": checks,
    }


def _wikidata_row(record: dict, path: Path, card: dict, report_sha: str) -> dict:
    statement = json.loads(record["public_claim_verbatim_quote"])
    enriched = {
        **record,
        "source_kind": "wikidata",
        "wikidata_rank": statement.get("rank"),
        "wikidata_reference_count": len(statement.get("references", [])),
        "wikidata_qualifier_count": sum(
            len(values) for values in statement.get("qualifiers", {}).values()
        ),
    }
    checks = {
        "claim_text": card.get("public_claim_text") == enriched["public_claim_text"],
        "verbatim_quote": card.get("public_claim_verbatim_quote")
        == enriched["public_claim_verbatim_quote"],
        "source_url": card.get("public_claim_source_url") == enriched["public_claim_source_url"],
        "locator": card.get("public_claim_locator") == enriched["public_claim_locator"],
        "source_sha256": card.get("public_claim_source_sha256")
        == enriched["public_claim_source_sha256"],
        "report_sha256": card.get("sanitized_report_sha256") == report_sha,
        "passed": card.get("result_status") == "PASSED_UNDER_PROTOCOL",
    }
    if not all(checks.values()):
        raise SystemExit(f"ERROR: card/manifest mismatch {card['evidence_id']}: {checks}")
    return {
        **enriched,
        "card": card,
        "card_path": path.relative_to(ROOT).as_posix(),
        "checks": checks,
    }
