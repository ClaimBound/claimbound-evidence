#!/usr/bin/env python3
"""Register a CB7K primary-source group in its existing registry slots."""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card
from claimbound_evidence.registry import _compute_statistics, validate_registry

REGISTRY = ROOT / "docs/registry/evidence_index.json"
CARDS = ROOT / "docs/evidence_cards"


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?", default=Path("artifacts/cb7k_dom001_t01_openai_primary_claims.json"))
    parser.add_argument("--skip-registry-validation", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    runner = (
        "python scripts/verify_primary_public_claim_group.py "
        f"{manifest_path.relative_to(ROOT).as_posix()} --source-file <local-raw-pdf>"
    )
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = {row["protocol_id"]: row for row in registry["cards"]}
    replacements: dict[str, dict] = {}
    for record in manifest["records"]:
        protocol_id = record["protocol_id"]
        previous_entry = entries[protocol_id]
        path = ROOT / previous_entry["path"]
        previous_card = json.loads(path.read_text(encoding="utf-8"))
        evidence_id = previous_card["evidence_id"]
        quote_sha = hashlib.sha256(
            record["public_claim_verbatim_quote"].encode("utf-8")
        ).hexdigest()
        card = {
            "access_date": manifest["access_date"],
            "ai_assistance": (
                "AI assisted source selection and deterministic quote extraction; the committed "
                "verifier checks the source hash and exact quote. No independent human semantic "
                "adjudication is claimed."
            ),
            "baseline_control_summary": (
                "The gate passes only when the full fetched response SHA-256 matches and the "
                "exact quoted statement occurs in normalized source text."
            ),
            "card_svg_rendered": f"docs/evidence_cards/{evidence_id}.svg",
            "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
            "claim_boundary": manifest["claim_boundary"],
            "claim_type": "primary_source_public_statement",
            "created_at": manifest["access_date"],
            "domain": previous_card["domain"],
            "evidence_id": evidence_id,
            "evidence_url": (
                "https://github.com/ClaimBound/claimbound-evidence/blob/main/"
                f"docs/evidence_cards/{evidence_id}.json"
            ),
            "execution_mode": "AUTOMATED_AI_ASSISTED",
            "git_commit": "local-before-merge",
            "known_limitations": [
                "This retrospective audit was not preregistered before source inspection.",
                "The result verifies publication and byte identity, not independent ground truth.",
                (
                    f"The source is the named publisher's own document ({manifest['source_name']}); "
                    "the card does not provide independent corroboration of its statements."
                ),
                "A future PDF edit produces source drift until a separately documented rerun.",
            ],
            "last_verified_date": manifest["access_date"],
            "manual_review": (
                f"Source locator recorded as {record['section_locator']}. Automated verification "
                "requires the exact quote in the hash-bound source; independent human semantic "
                "review is not registered."
            ),
            "official_source_name": manifest["source_name"],
            "official_source_url": manifest["source_url"],
            "operator": manifest["operator"],
            "protocol_id": protocol_id,
            "protocol_version": manifest["protocol_version"],
            "public_claim_text": record["public_claim_text"],
            "public_claim_verbatim_quote": record["public_claim_verbatim_quote"],
            "public_claim_source_url": manifest["source_url"],
            "public_claim_locator": record["section_locator"],
            "public_claim_captured_at": manifest["access_date"],
            "public_claim_source_sha256": manifest["source_sha256"],
            "public_claim_quote_sha256": quote_sha,
            "raw_payload_committed": False,
            "raw_payload_manifest": (
                f"source SHA-256 {manifest['source_sha256']}; quote SHA-256 {quote_sha}; "
                "raw PDF retained outside the public repository"
            ),
            "record_type": "source_audit",
            "registry_sequence": previous_card["registry_sequence"],
            "reproduction_level": "not independently reproduced",
            "result_status": manifest["result_status"],
            "runner_command": runner,
            "sanitized_report_path": manifest_path.relative_to(ROOT).as_posix(),
            "sanitized_report_sha256": report_sha,
            "source_rights_note": (
                "Named public primary source; only limited quotes, locators, and hashes are committed."
            ),
            "verification_count": 1,
            "verification_level": "SINGLE_OPERATOR",
            "visual_summary": {
                "allowed_claim_sentence": record["public_claim_text"],
                "artifact_ref": record["section_locator"],
                "candidate_definition": "one exact statement in the named primary source",
                "controls_and_gate": "exact quote + complete response SHA-256",
                "period_scope": f"source fetched on {manifest['access_date']}",
                "target_definition": f"{manifest['source_name']} public statements",
            },
        }
        violations = validate_evidence_card(card)
        if violations:
            raise SystemExit(f"ERROR: {protocol_id}: {'; '.join(violations)}")
        path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        path.with_suffix(".svg").write_text(render_svg(path), encoding="utf-8")
        replacements[protocol_id] = registry_entry(card, path, previous_entry)
    registry["cards"] = [
        replacements.get(row["protocol_id"], row) for row in registry["cards"]
    ]
    registry["statistics"] = _compute_statistics(registry["cards"])
    registry["last_updated"] = manifest["access_date"]
    REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not args.skip_registry_validation:
        violations = validate_registry(registry, ROOT)
        if violations:
            raise SystemExit("ERROR: registry invalid: " + "; ".join(violations[:20]))
    protocols = sorted(replacements)
    print(f"REGISTERED: {len(protocols)} primary-source public claims in {protocols[0].rsplit('-', 1)[0]} slots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
