#!/usr/bin/env python3
"""Reproduce the historical first-run format used by late CB7K batches.

Generic first-run (create) counterpart to ``readjudicate_claim_batch.py``, which
only re-adjudicates batches that already have registered cards. This reuses the
same committed adjudication logic — ``locate_gate`` and ``redirect_is_drift`` —
so outcomes are fixed by one predicate across every batch, not by a per-batch
hand-authored locator matrix. The historical workflow asserted that sources were
selected before freezing by accessibility and topic relevance only and were not
substituted after the run; the published artifacts do not independently prove
that ordering.

This runner is retained for historical reproducibility. Its execution manifests
do not contain the ``source_role`` or ``selection_provenance`` fields required by
the current completion validator, so it must not be used to claim current
ClaimBound protocol compliance or as the template for a new campaign.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from build_public_claim_catalog import GATE_METHODS, domains, make_claims, validate
from claimbound_gate_locator import locate_gate
from readjudicate_claim_batch import (
    EXECUTION_REQUIRED_GATES,
    extraction_quality,
    missing_source_integrity_fields,
    redirect_is_drift,
    statistics,
)
from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs/evidence_cards"
REGISTRY = ROOT / "docs/registry/evidence_index.json"

GATE_TARGETS = {
    "source-integrity": "The frozen bytes identify an exact public source and a topic-specific boundary for {topic}.",
    "numerator-denominator": "A numeric result for {topic} discloses numerator, denominator, units, exclusions and rounding.",
    "coverage": "The source states population, scope, exclusions or limitations for {topic}.",
    "time-boundary": "The source fixes a date, period or version for {topic}.",
    "method-version": "The source identifies the method and applicable version for {topic}.",
    "comparator": "The source identifies a comparable baseline and measurement rule for {topic}.",
    "reproducibility": "A public operator can obtain inputs and rerun the {topic} procedure.",
    "negative-evidence": "The boundary includes limitations, failures or contradictory evidence for {topic}.",
    "conflicts-disclosure": "The boundary identifies the institution responsible for the {topic} report.",
    "overclaim-drift": "The source contains a caveat preventing a universal {topic} guarantee.",
}


def adjudicate(claim: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Return the status decision using the committed gate predicate."""
    gate = str(claim["gate"])
    decision = locate_gate(source["text"], str(claim["topic"]), gate)
    locator = decision.locator
    missing = list(decision.missing_facets)

    if source["http_status"] != 200:
        status = "BLOCKED_SOURCE"
        locator = f"HTTP {source['http_status']}"
        basis = "The exact frozen URL was inaccessible; no replacement was selected."
        reason = (
            "STALE_OR_INCORRECT_EXACT_URL" if source["http_status"] == 404
            else "ACCESS_POLICY_OR_ANTI_BOT" if source["http_status"] in {401, 403, 429, 444}
            else "TRANSPORT_FAILURE" if source["http_status"] == 0
            else "OTHER_HTTP_FAILURE"
        )
    elif redirect_is_drift(source["source_url"], source["final_url"]):
        status = "SOURCE_DRIFT"
        locator = f"selected={source['source_url']} canonical={source['final_url']}"
        basis = "The frozen URL resolved outside its selected source boundary."
        reason = "SOURCE_BOUNDARY_DRIFT"
    elif gate == "source-integrity":
        missing = missing_source_integrity_fields(source)
        locator = (
            f"SHA-256 {source['sha256']}; selected={source['source_url']}; "
            f"final={source['final_url']}"
        )
        if missing:
            status = "INSUFFICIENT_COVERAGE"
            basis = "The response bytes were frozen, but the source-integrity provenance record is incomplete."
            reason = "SOURCE_INTEGRITY_METADATA_INCOMPLETE"
        else:
            status = "PASSED_UNDER_PROTOCOL"
            basis = "The frozen manifest records the exact selected URL, final URL, redirect chain, access timestamp, and response hash."
            reason = "SOURCE_BOUNDARY_VERIFIED"
    elif gate in EXECUTION_REQUIRED_GATES:
        status = "INSUFFICIENT_COVERAGE"
        locator = locator or (source["text"].splitlines() or ["empty extraction"])[0]
        reason = "EXECUTION_ARTIFACT_MISSING" if decision.locator else "GATE_FACETS_AND_EXECUTION_ARTIFACT_MISSING"
        basis = "Text disclosure alone cannot pass this executable gate; no independent numeric reproduction, method execution, or rerun artifact was recorded."
    elif locator:
        status = "PASSED_UNDER_PROTOCOL"
        basis = "Gate-aware review found a topic-specific verbatim sentence satisfying the gate predicate."
        reason = "COMPLETE_TEXTUAL_GATE_FACETS"
    else:
        status = "INSUFFICIENT_COVERAGE"
        locator = (source["text"].splitlines() or ["empty extraction"])[0]
        basis = "No topic-specific verbatim sentence satisfied the gate predicate."
        reason = "VERY_SHORT_OR_SHELL_EXTRACTION" if len(source["text"].strip()) < 500 else "GATE_SPECIFIC_FACETS_MISSING"

    return {
        "status": status,
        "locator": locator,
        "review_basis": basis,
        "reason_code": reason,
        "missing_facets": missing,
        "extraction_quality": extraction_quality(source["text"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--domains", nargs="+", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--meta-root", type=Path, required=True)
    parser.add_argument("--text-root", type=Path, required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--access-date", required=True, help="YYYY-MM-DD, must match the fetch date")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    sources = {row["key"]: row for row in manifest["sources"]}
    catalog_domains = domains()
    catalog = make_claims(catalog_domains)
    validate(catalog_domains, catalog)
    claims = [c for c in catalog if c["domain_code"] in set(args.domains)]
    expected_claims = 70 * len(args.domains)
    if len(claims) != expected_claims or len(sources) != len(args.domains) * 7:
        raise SystemExit(
            f"expected exactly {expected_claims} claims and {len(args.domains) * 7} frozen sources"
        )

    registry = json.loads(REGISTRY.read_text())
    existing_ids = {c["evidence_id"] for c in registry["cards"]}
    already_registered = [
        c["claim_id"] for c in claims
        if f"CLAIMBOUND-{c['claim_id']}-{args.access_date}" in existing_ids
    ]
    if already_registered:
        raise SystemExit(
            f"issue {args.issue} already has {len(already_registered)} registered cards "
            f"(e.g. {already_registered[0]}); refusing to re-register. "
            "Use readjudicate_claim_batch.py to re-adjudicate an existing batch instead."
        )

    protocol = f"CB7K-ISSUE-{args.issue}-GATE-AWARE-FIRST-RUN-{args.access_date}-v1"
    report_path = ROOT / f"artifacts/claim_batch_{args.issue}_manual_review.json"
    execution_path = ROOT / f"artifacts/claim_batch_{args.issue}_execution_manifest.json"

    source_rows: dict[str, dict[str, Any]] = {}
    for key, frozen in sources.items():
        meta = json.loads((args.meta_root / f"{key}.json").read_text())
        source_rows[key] = {
            **frozen,
            **meta,
            "final_url": meta.get("final_url") or frozen["source_url"],
            "sha256": hashlib.sha256((args.raw_root / f"{key}.bin").read_bytes()).hexdigest(),
            "text": (args.text_root / f"{key}.txt").read_text(errors="replace"),
        }

    manifest_sha = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    execution, rows = [], []
    for claim in claims:
        key = f"{claim['domain_code']}-T{claim['topic_index']:02d}"
        source = source_rows[key]
        gate = str(claim["gate"])
        target = GATE_TARGETS[gate].format(topic=claim["topic"])
        decision = adjudicate(claim, source)
        execution.append({
            "claim_id": claim["claim_id"],
            "source_url": source["source_url"],
            "evaluation_method": GATE_METHODS[gate],
            "frozen_parameters": {"topic": claim["topic"], "gate": gate},
            "support_rule": target,
            "negative_rule": claim["adjudication_rule"],
        })
        rows.append({**claim, **decision, "target_statement": target,
                     "source_url": source["source_url"], "canonical_url": source["final_url"],
                     "http_status": source["http_status"], "source_sha256": source["sha256"]})

    execution_path.write_text(json.dumps({
        "issue_number": args.issue,
        "source_manifest_sha256": manifest_sha,
        "claim_boundary": f"Claim-level execution plan for issue #{args.issue} only; it is not evidence and predeclares no outcome.",
        "raw_payload_committed": False,
        "entries": execution,
    }, indent=2, ensure_ascii=False) + "\n")

    counts = dict(Counter(r["status"] for r in rows))
    report_path.write_text(json.dumps({
        "issue_number": args.issue,
        "protocol_version": protocol,
        "source_manifest_sha256": manifest_sha,
        "claim_boundary": (
            f"Gate-aware first-run adjudication of 21 preregistered topic sources for issue #{args.issue}; "
            "sources selected before freezing by accessibility and topic relevance only; no source replaced "
            "after observation."
        ),
        "operator": args.operator,
        "raw_payload_committed": False,
        "review_method": (
            "complete topic-specific textual gate facets with verbatim locators; numerator-denominator, "
            "method-version, and reproducibility additionally require an independent execution artifact"
        ),
        "result_counts": counts,
        "cards": rows,
    }, indent=2, ensure_ascii=False) + "\n")
    report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()

    registry = json.loads(REGISTRY.read_text())
    sequence = max(x["registry_sequence"] for x in registry["cards"])
    new_entries = []
    for row in rows:
        sequence += 1
        eid = f"CLAIMBOUND-{row['claim_id']}-{args.access_date}"
        missing = f" Missing facets: {', '.join(row['missing_facets'])}." if row["missing_facets"] else ""
        card = {
            "access_date": args.access_date,
            "ai_assistance": "AI-assisted extraction and gate-facet location; outcomes are fixed by the committed locate_gate predicate.",
            "card_svg_rendered": f"docs/evidence_cards/{eid}.svg",
            "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
            "claim_boundary": row["target_statement"] + " This card is limited to one preregistered source boundary.",
            "claim_type": "source_boundary",
            "created_at": args.access_date,
            "domain": row["domain_slug"],
            "evidence_id": eid,
            "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json",
            "execution_mode": "AUTOMATED_AI_ASSISTED",
            "git_commit": "local-before-merge",
            "known_limitations": [
                "One exact source boundary only; no domain-wide certification.",
                "A pass applies only to the named gate and verbatim locator.",
                "Insufficient coverage is not a negative result.",
            ],
            "last_verified_date": args.access_date,
            "manual_review": f"{row['review_basis']} Reason: {row['reason_code']}.{missing} Extraction: {row['extraction_quality']}. Locator: {row['locator']}",
            "official_source_name": f"Official public source {row['domain_code']}-T{row['topic_index']:02d} ({row['topic']})",
            "official_source_url": row["source_url"],
            "operator": args.operator,
            "protocol_id": row["claim_id"],
            "protocol_version": protocol,
            "raw_payload_committed": False,
            "raw_payload_manifest": f"HTTP {row['http_status']}; canonical {row['canonical_url']}; SHA-256 {row['source_sha256']}; source manifest {manifest_sha}; raw bytes retained locally only",
            "record_type": "source_audit",
            "registry_sequence": sequence,
            "reproduction_level": "not independently reproduced",
            "result_status": row["status"],
            "runner_command": f"python scripts/claimbound_run_claim_batch.py --issue {args.issue} --domains {' '.join(args.domains)} --manifest <local> --raw-root <local> --meta-root <local> --text-root <local> --operator <handle> --access-date {args.access_date}",
            "sanitized_report_path": str(report_path.relative_to(ROOT)),
            "sanitized_report_sha256": report_sha,
            "source_rights_note": "Public documentation source; raw response bytes are not committed.",
            "verification_count": 1,
            "verification_level": "SINGLE_OPERATOR",
        }
        if row["status"] == "PASSED_UNDER_PROTOCOL":
            card["baseline_control_summary"] = f"Gate-aware review passed only at verbatim locator: {row['locator']}"
        elif row["status"] == "BLOCKED_SOURCE":
            card["block_reason"] = row["review_basis"]
        elif row["status"] == "SOURCE_DRIFT":
            card["drift_reason"] = row["review_basis"]
        violations = validate_evidence_card(card)
        if violations:
            raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path = CARDS / f"{eid}.json"
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
        (CARDS / f"{eid}.svg").write_text(render_svg(path))
        new_entries.append({
            **{k: card[k] for k in ("evidence_id", "registry_sequence", "result_status", "protocol_id", "domain", "record_type", "operator", "created_at", "last_verified_date", "verification_level", "verification_count", "reproduction_level", "official_source_name", "sanitized_report_path")},
            "path": str(path.relative_to(ROOT)),
        })

    registry["cards"].extend(new_entries)
    registry["cards"].sort(key=lambda x: x["evidence_id"])
    registry["card_count"] = len(registry["cards"])
    registry["statistics"] = statistics(registry["cards"])
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"issue": args.issue, "reviewed_cards": len(rows), "result_counts": counts,
                      "registry_card_count": registry["card_count"], "report_sha256": report_sha}, indent=2))


if __name__ == "__main__":
    main()
