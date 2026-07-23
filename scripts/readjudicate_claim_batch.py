#!/usr/bin/env python3
"""Re-adjudicate an existing claim batch with gate-aware verbatim locators."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from build_public_claim_catalog import domains, make_claims, validate
from claimbound_gate_locator import locate_gate
from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs/evidence_cards"
REGISTRY = ROOT / "docs/registry/evidence_index.json"
EXECUTION_REQUIRED_GATES = {
    "numerator-denominator",
    "method-version",
    "reproducibility",
}


def redirect_is_drift(selected: str, final: str) -> bool:
    """Distinguish a recorded canonical redirect from a changed source boundary."""
    if selected == final:
        return False
    selected_host = urlparse(selected).hostname or ""
    final_host = urlparse(final).hostname or ""
    selected_base = ".".join(selected_host.removeprefix("www.").split(".")[-2:])
    final_base = ".".join(final_host.removeprefix("www.").split(".")[-2:])
    final_path = urlparse(final).path.casefold()
    return selected_base != final_base or any(marker in final_path for marker in ("/404", "/error/", "/not-found"))


def statistics(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        name: dict(sorted(Counter(x[field] for x in entries).items()))
        for name, field in (
            ("by_domain", "domain"),
            ("by_record_type", "record_type"),
            ("by_result_status", "result_status"),
            ("by_source", "official_source_name"),
        )
    }


def extraction_quality(text: str) -> str:
    length = len(text.strip())
    if length < 100:
        return "EMPTY_OR_SHELL_UNDER_100_CHARS"
    if length < 500:
        return "VERY_SHORT_UNDER_500_CHARS"
    if length < 2_000:
        return "SHORT_UNDER_2000_CHARS"
    return "TEXT_EXTRACT_AT_LEAST_2000_CHARS"


def missing_source_integrity_fields(source: dict[str, Any]) -> list[str]:
    missing = []
    if not source.get("accessed_at_utc"):
        missing.append("accessed-at-utc")
    redirect_chain = source.get("redirect_chain")
    if not isinstance(redirect_chain, list):
        missing.append("redirect-chain")
    elif source.get("source_url") != source.get("final_url") and not redirect_chain:
        missing.append("redirect-chain")
    if not source.get("sha256"):
        missing.append("response-sha256")
    if not source.get("source_url") or not source.get("final_url"):
        missing.append("selected-and-final-url")
    return missing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--domains", nargs="+", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--meta-root", type=Path, required=True)
    parser.add_argument("--text-root", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    sources = {row["key"]: row for row in manifest["sources"]}
    catalog_domains = domains()
    catalog = make_claims(catalog_domains)
    validate(catalog_domains, catalog)
    claims = [claim for claim in catalog if claim["domain_code"] in set(args.domains)]
    if len(claims) != 210 or len(sources) != 21:
        raise SystemExit("expected exactly 210 claims and 21 frozen sources")

    source_rows: dict[str, dict[str, Any]] = {}
    for key, frozen in sources.items():
        raw_path = args.raw_root / f"{key}.bin"
        meta = json.loads((args.meta_root / f"{key}.json").read_text())
        source_rows[key] = {
            **frozen,
            **meta,
            "final_url": meta.get("final_url") or meta.get("canonical_url") or frozen["source_url"],
            "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "text": (args.text_root / f"{key}.txt").read_text(errors="replace"),
        }

    rows: list[dict[str, Any]] = []
    for claim in claims:
        key = f"{claim['domain_code']}-T{claim['topic_index']:02d}"
        source = source_rows[key]
        gate = claim["gate"]
        gate_decision = locate_gate(source["text"], str(claim["topic"]), str(gate))
        locator = gate_decision.locator
        missing_facets = list(gate_decision.missing_facets)
        if source["http_status"] != 200:
            status = "BLOCKED_SOURCE"
            locator = f"HTTP {source['http_status']}"
            basis = "The exact frozen URL was inaccessible; no replacement was selected."
            reason_code = (
                "STALE_OR_INCORRECT_EXACT_URL"
                if source["http_status"] == 404
                else "ACCESS_POLICY_OR_ANTI_BOT"
                if source["http_status"] in {401, 403, 429, 444}
                else "TRANSPORT_FAILURE"
                if source["http_status"] == 0
                else "OTHER_HTTP_FAILURE"
            )
        elif redirect_is_drift(source["source_url"], source["final_url"]):
            status = "SOURCE_DRIFT"
            locator = f"selected={source['source_url']} canonical={source['final_url']}"
            basis = "The frozen URL resolved outside its selected source boundary."
            reason_code = "SOURCE_BOUNDARY_DRIFT"
        elif gate == "source-integrity":
            missing_facets = missing_source_integrity_fields(source)
            locator = (
                f"SHA-256 {source['sha256']}; selected={source['source_url']}; "
                f"final={source['final_url']}"
            )
            if missing_facets:
                status = "INSUFFICIENT_COVERAGE"
                basis = (
                    "The response bytes were frozen, but the source-integrity "
                    "provenance record is incomplete."
                )
                reason_code = "SOURCE_INTEGRITY_METADATA_INCOMPLETE"
            else:
                status = "PASSED_UNDER_PROTOCOL"
                basis = (
                    "The frozen manifest records the exact selected URL, final URL, "
                    "redirect chain, access timestamp, and response hash."
                )
                reason_code = "SOURCE_BOUNDARY_VERIFIED"
        elif gate in EXECUTION_REQUIRED_GATES:
            status = "INSUFFICIENT_COVERAGE"
            locator = locator or (source["text"].splitlines() or ["empty extraction"])[0]
            reason_code = (
                "EXECUTION_ARTIFACT_MISSING"
                if gate_decision.locator
                else "GATE_FACETS_AND_EXECUTION_ARTIFACT_MISSING"
            )
            basis = (
                "Text disclosure alone cannot pass this executable gate; no independent "
                "numeric reproduction, method execution, or rerun artifact was recorded."
            )
        elif locator:
            status = "PASSED_UNDER_PROTOCOL"
            basis = "Gate-aware review found a topic-specific verbatim sentence satisfying the gate predicate."
            reason_code = "COMPLETE_TEXTUAL_GATE_FACETS"
        else:
            status = "INSUFFICIENT_COVERAGE"
            locator = (source["text"].splitlines() or ["empty extraction"])[0]
            basis = "No topic-specific verbatim sentence satisfied the gate predicate."
            reason_code = (
                "VERY_SHORT_OR_SHELL_EXTRACTION"
                if len(source["text"].strip()) < 500
                else "GATE_SPECIFIC_FACETS_MISSING"
            )
        rows.append(
            {
                **claim,
                "status": status,
                "locator": locator,
                "review_basis": basis,
                "reason_code": reason_code,
                "missing_facets": missing_facets,
                "extraction_quality": extraction_quality(source["text"]),
                "source_url": source["source_url"],
                "canonical_url": source["final_url"],
                "http_status": source["http_status"],
                "source_sha256": source["sha256"],
            }
        )

    report_path = ROOT / f"artifacts/claim_batch_{args.issue}_manual_review.json"
    report = {
        "issue_number": args.issue,
        "protocol_version": f"CB7K-ISSUE-{args.issue}-GATE-AWARE-READJUDICATION-2026-07-23-v3",
        "source_manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "claim_boundary": "Gate-aware re-adjudication of the original frozen sources; no source was replaced after observation.",
        "raw_payload_committed": False,
        "review_method": (
            "complete topic-specific textual gate facets with verbatim locators; "
            "numerator-denominator, method-version, and reproducibility additionally "
            "require an independent execution artifact"
        ),
        "result_counts": dict(Counter(row["status"] for row in rows)),
        "cards": rows,
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()

    registry = json.loads(REGISTRY.read_text())
    registry_by_protocol = {entry["protocol_id"]: entry for entry in registry["cards"]}
    for row in rows:
        matches = list(CARDS.glob(f"CLAIMBOUND-{row['claim_id']}-*.json"))
        if len(matches) != 1:
            raise SystemExit(f"{row['claim_id']}: expected one existing card, found {len(matches)}")
        path = matches[0]
        card = json.loads(path.read_text())
        card["result_status"] = row["status"]
        card["protocol_version"] = report["protocol_version"]
        missing = (
            f" Missing facets: {', '.join(row['missing_facets'])}."
            if row["missing_facets"]
            else ""
        )
        card["manual_review"] = (
            f"{row['review_basis']} Reason: {row['reason_code']}."
            f"{missing} Extraction: {row['extraction_quality']}. Locator: {row['locator']}"
        )
        card["sanitized_report_sha256"] = report_sha
        card.pop("baseline_control_summary", None)
        card.pop("block_reason", None)
        card.pop("drift_reason", None)
        if row["status"] == "PASSED_UNDER_PROTOCOL":
            card["baseline_control_summary"] = (
                f"Gate-aware review passed only at audit locator: {row['locator']}"
                if row["gate"] == "source-integrity"
                else f"Gate-aware review passed only at verbatim locator: {row['locator']}"
            )
        elif row["status"] == "BLOCKED_SOURCE":
            card["block_reason"] = row["review_basis"]
        elif row["status"] == "SOURCE_DRIFT":
            card["drift_reason"] = row["review_basis"]
        violations = validate_evidence_card(card)
        if violations:
            raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
        path.with_suffix(".svg").write_text(render_svg(path))
        registry_by_protocol[row["claim_id"]]["result_status"] = row["status"]

    registry["statistics"] = statistics(registry["cards"])
    registry["card_count"] = len(registry["cards"])
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"issue": args.issue, "result_counts": report["result_counts"]}, indent=2))


if __name__ == "__main__":
    main()
