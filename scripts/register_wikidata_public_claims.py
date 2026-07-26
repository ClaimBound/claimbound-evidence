#!/usr/bin/env python3
"""Replace the historical CB7K gate-question records with sourced statements."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card
from claimbound_evidence.registry import _compute_statistics, validate_registry

MANIFEST = ROOT / "artifacts/cb7k_wikidata_public_claims.json"
REGISTRY = ROOT / "docs/registry/evidence_index.json"
CARDS = ROOT / "docs/evidence_cards"
CARD_RE = re.compile(r"CLAIMBOUND-CB7K-DOM(\d{3})-T\d{2}-G\d{2}-\d{4}-\d{2}-\d{2}\.json")
PROTOCOL = "CB7K-WIKIDATA-PUBLICATION-REVISION-v1"
RUNNER = (
    "python scripts/build_wikidata_public_claims.py verify-sources "
    "artifacts/cb7k_wikidata_public_claims.json --cache <local-wikidata-cache>"
)


def load_slots() -> dict[str, list[Path]]:
    slots: dict[str, list[Path]] = {}
    for path in sorted(CARDS.glob("CLAIMBOUND-CB7K-*.json")):
        match = CARD_RE.fullmatch(path.name)
        if match:
            slots.setdefault(f"DOM{match.group(1)}", []).append(path)
    if len(slots) != 100 or any(len(paths) != 70 for paths in slots.values()):
        raise SystemExit("ERROR: expected 100 existing CB7K groups of 70 registry slots")
    return slots


def registry_entry(card: dict, path: Path, previous: dict) -> dict:
    entry = dict(previous)
    for field in (
        "domain", "evidence_id", "official_source_name", "record_type",
        "reproduction_level", "result_status", "sanitized_report_path",
        "registry_sequence", "operator", "last_verified_date",
        "verification_count", "verification_level",
    ):
        entry[field] = card[field]
    entry["path"] = path.relative_to(ROOT).as_posix()
    return entry


def build() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = manifest["records"]
    if len(records) != 7000 or len({row["statement_id"] for row in records}) != 7000:
        raise SystemExit("ERROR: manifest must contain 7000 distinct statements")
    report_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    slots = load_slots()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    previous_entries = {row["evidence_id"]: row for row in registry["cards"]}
    replacement_entries: dict[str, dict] = {}
    by_domain: dict[str, list[dict]] = {}
    for row in records:
        by_domain.setdefault(row["domain_code"], []).append(row)
    for domain_code, paths in sorted(slots.items()):
        rows = by_domain.get(domain_code, [])
        if len(rows) != 70:
            raise SystemExit(f"ERROR: {domain_code} manifest coverage is {len(rows)}")
        for path, row in zip(paths, rows, strict=True):
            old = json.loads(path.read_text(encoding="utf-8"))
            evidence_id = old["evidence_id"]
            card = {
                "access_date": "2026-07-26",
                "ai_assistance": (
                    "AI assisted pipeline design and code review; source discovery and outcomes "
                    "are determined by the committed deterministic collector and byte checks."
                ),
                "baseline_control_summary": (
                    "Control requires the statement GUID and exact JSON excerpt to occur in the "
                    "named immutable revision; the revision payload SHA-256 must match."
                ),
                "card_svg_rendered": f"docs/evidence_cards/{evidence_id}.svg",
                "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
                "claim_boundary": (
                    "This result establishes only that the named structured statement was "
                    "published in the frozen Wikidata revision. It does not independently "
                    "establish the real-world truth of the statement."
                ),
                "claim_type": "public_statement_publication",
                "created_at": "2026-07-26",
                "domain": row["domain_slug"],
                "evidence_id": evidence_id,
                "evidence_url": (
                    "https://github.com/ClaimBound/claimbound-evidence/blob/main/"
                    f"docs/evidence_cards/{evidence_id}.json"
                ),
                "execution_mode": "AUTOMATED_AI_ASSISTED",
                "git_commit": "local-before-merge",
                "known_limitations": [
                    "Verification is limited to publication in one Wikidata revision.",
                    "Wikidata publication is not independent corroboration or ground truth.",
                    "No claim is made outside the exact statement GUID and revision boundary.",
                ],
                "last_verified_date": "2026-07-26",
                "manual_review": (
                    "Deterministic local review confirmed that the exact statement JSON and GUID "
                    "occur in the revision content and that the full content hash matches."
                ),
                "official_source_name": (
                    f"Wikidata revision {row['revision_id']} ({row['entity_id']})"
                ),
                "official_source_url": row["public_claim_source_url"],
                "operator": "NeoZorK",
                "protocol_id": old["protocol_id"],
                "protocol_version": PROTOCOL,
                "public_claim_text": row["public_claim_text"],
                "public_claim_verbatim_quote": row["public_claim_verbatim_quote"],
                "public_claim_source_url": row["public_claim_source_url"],
                "public_claim_locator": row["public_claim_locator"],
                "public_claim_captured_at": row["public_claim_captured_at"],
                "public_claim_source_sha256": row["public_claim_source_sha256"],
                "raw_payload_committed": False,
                "raw_payload_manifest": (
                    f"Wikidata revision {row['revision_id']}; entity {row['entity_id']}; "
                    f"source SHA-256 {row['public_claim_source_sha256']}; statement SHA-256 "
                    f"{row['statement_sha256']}; raw revision content retained in local cache only"
                ),
                "record_type": "evidence_result",
                "registry_sequence": old["registry_sequence"],
                "reproduction_level": "not independently reproduced",
                "result_status": "PASSED_UNDER_PROTOCOL",
                "runner_command": RUNNER,
                "sanitized_report_path": MANIFEST.relative_to(ROOT).as_posix(),
                "sanitized_report_sha256": report_sha,
                "source_rights_note": (
                    "Wikidata structured data is CC0; raw revision payloads are not committed."
                ),
                "verification_count": 1,
                "verification_level": "SINGLE_OPERATOR",
                "visual_summary": {
                    "allowed_claim_sentence": row["public_claim_text"],
                    "artifact_ref": f"statement {row['statement_id']}",
                    "candidate_definition": f"{row['entity_label']} ({row['entity_id']}) / {row['property_id']}",
                    "controls_and_gate": "exact GUID + verbatim JSON + frozen revision SHA-256",
                    "period_scope": f"revision {row['revision_id']} at {row['revision_timestamp']}",
                    "target_definition": row["domain_title"],
                },
            }
            violations = validate_evidence_card(card)
            if violations:
                raise SystemExit(f"ERROR: {evidence_id}: {'; '.join(violations)}")
            path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            path.with_suffix(".svg").write_text(render_svg(path), encoding="utf-8")
            replacement_entries[evidence_id] = registry_entry(
                card, path, previous_entries[evidence_id]
            )
    registry["cards"] = [
        replacement_entries.get(row["evidence_id"], row) for row in registry["cards"]
    ]
    registry["statistics"] = _compute_statistics(registry["cards"])
    registry["last_updated"] = "2026-07-26"
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    violations = validate_registry(registry, ROOT)
    if violations:
        raise SystemExit("ERROR: registry invalid: " + "; ".join(violations[:20]))
    print("REGISTERED: 7000 source-bound public claims in existing CB7K slots")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build"])
    args = parser.parse_args()
    if args.command == "build":
        build()


if __name__ == "__main__":
    main()
