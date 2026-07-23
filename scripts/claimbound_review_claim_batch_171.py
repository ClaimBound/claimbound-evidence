#!/usr/bin/env python3
"""Publish conservatively reviewed issue #171 source-boundary cards."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from build_public_claim_catalog import GATE_METHODS, domains, make_claims, validate
from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs/evidence_cards"
REGISTRY = ROOT / "docs/registry/evidence_index.json"
REPORT = ROOT / "artifacts/claim_batch_171_manual_review.json"
EXECUTION = ROOT / "artifacts/claim_batch_171_execution_manifest.json"
PROTOCOL = "CB7K-ISSUE-171-CONSERVATIVE-LOCATOR-REVIEW-2026-07-23-v1"

SOURCE_NAMES = {
    "DOM016-T01": "CDC NNDSS case-surveillance process",
    "DOM016-T02": "CDC National Vital Statistics System",
    "DOM016-T03": "CDC excess-deaths methodology",
    "DOM016-T04": "CDC serology-surveillance page",
    "DOM016-T05": "CDC foodborne-outbreak overview",
    "DOM016-T06": "CDC National Immunization Surveys",
    "DOM016-T07": "CDC Office of Minority Health overview",
    "DOM017-T01": "NHS England A&E waiting-times statistics",
    "DOM017-T02": "CMS unplanned hospital visits data",
    "DOM017-T03": "CMS healthcare-associated infections data",
    "DOM017-T04": "CMS healthcare personnel vaccination data",
    "DOM017-T05": "NHS England bed availability and occupancy",
    "DOM017-T06": "NHS England cancelled elective operations",
    "DOM017-T07": "CMS hospital measure methodology",
    "DOM018-T01": "FDA prescription-medicine labeling FAQ",
    "DOM018-T02": "FDA Paxlovid integrated review",
    "DOM018-T03": "FDA Drug Trials Snapshots",
    "DOM018-T04": "FDA AEMS public dashboard",
    "DOM018-T05": "FDA boxed-warning labeling guidance",
    "DOM018-T06": "FDA Drug Trials Snapshots 2023 summary",
    "DOM018-T07": "FDA postmarketing surveillance programs",
}

# Every pass below is tied to a verbatim locator in the frozen local extraction.
# Sources absent from this matrix, and gates absent within a source, are insufficient.
LOCATORS: dict[str, dict[str, str]] = {
    "DOM016-T01": {
        "source-integrity": "How We Conduct Case Surveillance",
        "coverage": "local, regional, state, and territorial public health agencies",
        "method-version": "The national case surveillance system uses case reporting and case notification",
        "reproducibility": "Message Evaluation and Testing Service",
    },
    "DOM016-T02": {
        "source-integrity": "National Vital Statistics System (NVSS)",
        "coverage": "all 50 states, New York City, and the District of Columbia",
        "time-boundary": "Updated June 9, 2025",
        "method-version": "International Classification of Diseases",
        "negative-evidence": "Vital events occurring in the United States to non-U.S. residents and vital events occurring abroad to U.S. residents are excluded",
        "overclaim-drift": "comparison of death rates by cause of death across ICD revisions should be done with caution",
    },
    "DOM016-T03": {
        "source-integrity": "Excess Deaths Associated with COVID-19",
        "numerator-denominator": "The percent excess was defined as the number of excess deaths divided by the threshold",
        "coverage": "by week and jurisdiction",
        "time-boundary": "from February 1, 2020 to present",
        "method-version": "Farrington surveillance algorithms",
        "comparator": "difference between the observed count and one of two thresholds",
        "reproducibility": "Download datasets in CSV format",
        "negative-evidence": "data for the most recent week(s) are still likely to be incomplete",
        "overclaim-drift": "cannot be used to determine whether a given jurisdiction has fewer deaths than expected",
    },
    "DOM016-T05": {
        "source-integrity": "How Foodborne Outbreaks Happen",
        "method-version": "Outbreak Investigations",
    },
    "DOM016-T06": {
        "source-integrity": "About the National Immunization Surveys",
        "coverage": "children 19–35 months",
        "time-boundary": "As of October 2025",
        "method-version": "standard survey methodology",
        "reproducibility": "NIS-Teen Data and Documentation for 2015 to Present",
        "overclaim-drift": "Cell phone numbers are randomly selected",
    },
    "DOM016-T07": {
        "source-integrity": "Office of Minority Health",
        "coverage": "populations that have been disadvantaged by their social or economic status, geographic location, and environment",
        "method-version": "preventable differences in the burden of disease",
        "overclaim-drift": "Many populations experience health disparities",
    },
    "DOM017-T01": {
        "source-integrity": "A&E Attendances and Emergency Admissions",
        "coverage": "all A&E types, including Urgent Treatment Centres, Minor Injury Units and Walk-in Centres",
        "time-boundary": "previous month",
        "method-version": "number discharged, admitted or transferred within four hours of arrival",
        "comparator": "comparisons to months in previous years",
        "negative-evidence": "should only be considered as an estimate",
    },
    "DOM017-T05": {
        "source-integrity": "Bed Availability and Occupancy",
        "coverage": "Bed Availability and Occupancy Data – Overnight",
    },
    "DOM017-T06": {
        "source-integrity": "Cancelled Elective Operations Data",
        "coverage": "number of cancelled elective operations and breaches of the standard",
        "time-boundary": "2025/26",
        "reproducibility": "CSV Full Extract",
        "negative-evidence": "collection was paused in April 2020",
    },
    "DOM017-T07": {
        "source-integrity": "Measure Methodology",
        "coverage": "hospital quality improvement, public reporting and payment purposes",
        "method-version": "Version number",
        "reproducibility": "measure methodology reports",
    },
    "DOM018-T01": {
        "source-integrity": "Frequently asked questions about labeling for prescription medicines",
        "coverage": "FDA-approved uses that are supported by substantial evidence of effectiveness, with benefits that outweigh risks",
        "method-version": "Full Prescribing Information",
        "reproducibility": "Structured Product Labeling",
        "negative-evidence": "serious adverse reactions",
        "overclaim-drift": "Situations when the risk from use clearly outweighs any possible therapeutic benefit",
    },
    "DOM018-T02": {
        "source-integrity": "Integrated Review",
        "numerator-denominator": "5.6% absolute reduction and an 86% relative reduction",
        "coverage": "outpatients with mild-to-moderate COVID-19",
        "method-version": "EPIC-HR",
        "comparator": "compared to placebo",
        "negative-evidence": "Data Reliability Issues at Specific Clinical Trial Sites",
        "overclaim-drift": "risk of serious adverse reactions due to drug-drug interactions",
    },
    "DOM018-T03": {
        "source-integrity": "Drug Trials Snapshots",
        "coverage": "approved New Molecular Entities (NMEs) and original biologics",
        "time-boundary": "published within 30 days of approval",
        "reproducibility": "MORE INFO",
        "negative-evidence": "Limitations of Snapshots",
        "overclaim-drift": "contain information that was available at the time of approval",
    },
    "DOM018-T05": {
        "source-integrity": "WARNINGS AND PRECAUTIONS SECTION",
        "coverage": "When to Use a Boxed Warning",
        "method-version": "§ 201.57(c)(1)",
        "negative-evidence": "Serious Adverse Reactions",
    },
    "DOM018-T07": {
        "source-integrity": "Postmarketing Surveillance Programs",
        "coverage": "all approved drug and therapeutic biologic products",
        "method-version": "FDA Adverse Event Reporting System",
        "negative-evidence": "all possible side effects of a drug can't be anticipated",
        "overclaim-drift": "premarket review",
    },
}

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


def source_key(claim: dict[str, Any]) -> str:
    return f"{claim['domain_code']}-T{claim['topic_index']:02d}"


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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--raw-root", type=Path, required=True)
    p.add_argument("--meta-root", type=Path, required=True)
    p.add_argument("--text-root", type=Path, required=True)
    p.add_argument("--operator", required=True)
    args = p.parse_args()

    manifest = json.loads(args.manifest.read_text())
    sources = {x["key"]: x for x in manifest["sources"]}
    if len(sources) != 21 or any(len({x["source_url"] for x in manifest["sources"] if x["key"].startswith(d)}) < 7 for d in ("DOM016", "DOM017", "DOM018")):
        raise SystemExit("expected seven independently frozen topic URLs per domain")

    manifest_sha = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    ds = domains()
    catalog = make_claims(ds)
    validate(ds, catalog)
    claims = [c for c in catalog if c["domain_code"] in {"DOM016", "DOM017", "DOM018"}]

    source_rows = {}
    for key, source in sources.items():
        raw = args.raw_root / f"{key}.bin"
        meta = json.loads((args.meta_root / f"{key}.json").read_text())
        source_rows[key] = {
            **source,
            **meta,
            "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
            "text": (args.text_root / f"{key}.txt").read_text(errors="replace"),
        }

    execution, rows = [], []
    for claim in claims:
        key = source_key(claim)
        source = source_rows[key]
        gate = claim["gate"]
        target = GATE_TARGETS[gate].format(topic=claim["topic"])
        execution.append(
            {
                "claim_id": claim["claim_id"],
                "source_url": source["source_url"],
                "evaluation_method": GATE_METHODS[gate],
                "frozen_parameters": {"topic": claim["topic"], "gate": gate},
                "support_rule": target,
                "negative_rule": claim["adjudication_rule"],
            }
        )

        if source["http_status"] != 200:
            decision = {
                "status": "BLOCKED_SOURCE",
                "locator": f"HTTP {source['http_status']}",
                "review_basis": "The exact preregistered URL was inaccessible; no replacement was selected.",
            }
        elif source["final_url"] != source["source_url"]:
            decision = {
                "status": "SOURCE_DRIFT",
                "locator": f"selected={source['source_url']} canonical={source['final_url']}",
                "review_basis": "The frozen URL resolved outside its selected source boundary.",
            }
        elif key in LOCATORS and gate in LOCATORS[key]:
            locator = LOCATORS[key][gate]
            if locator.casefold() not in source["text"].casefold():
                raise SystemExit(f"{claim['claim_id']}: absent locator {locator!r}")
            decision = {
                "status": "PASSED_UNDER_PROTOCOL",
                "locator": locator,
                "review_basis": "Manual conservative review found the required disclosure at this verbatim locator.",
            }
        else:
            locator = LOCATORS.get(key, {}).get("source-integrity", (source["text"].splitlines() or ["empty extraction"])[0])
            decision = {
                "status": "INSUFFICIENT_COVERAGE",
                "locator": locator,
                "review_basis": "The frozen source was reviewed but did not expose complete gate-specific evidence; absence was not converted into a negative result.",
            }

        rows.append(
            {
                **claim,
                **decision,
                "target_statement": target,
                "source_name": SOURCE_NAMES[key],
                "source_url": source["source_url"],
                "canonical_url": source["final_url"],
                "http_status": source["http_status"],
                "source_sha256": source["sha256"],
            }
        )

    EXECUTION.write_text(
        json.dumps(
            {
                "issue_number": 171,
                "source_manifest_sha256": manifest_sha,
                "claim_boundary": "Claim-level execution plan for issue #171 only; it is not evidence and predeclares no outcome.",
                "raw_payload_committed": False,
                "entries": execution,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    counts = dict(Counter(x["status"] for x in rows))
    REPORT.write_text(
        json.dumps(
            {
                "issue_number": 171,
                "protocol_version": PROTOCOL,
                "source_manifest_sha256": manifest_sha,
                "claim_boundary": "Conservative manual review of 21 preregistered public-health, hospital and pharmaceutical topic URLs for issue #171; no source replacement after observation.",
                "operator": args.operator,
                "raw_payload_committed": False,
                "review_method": "explicit gate-to-verbatim-locator matrix; unreviewed or incomplete gates remain insufficient",
                "result_counts": counts,
                "cards": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    report_sha = hashlib.sha256(REPORT.read_bytes()).hexdigest()
    registry = json.loads(REGISTRY.read_text())
    sequence = max(x["registry_sequence"] for x in registry["cards"])
    new_entries = []
    for row in rows:
        sequence += 1
        eid = f"CLAIMBOUND-{row['claim_id']}-2026-07-23"
        limitations = [
            "One exact source boundary only; no domain-wide certification.",
            "A pass applies only to the named gate and verbatim locator.",
            "Insufficient coverage is not a negative result.",
        ]
        card = {
            "access_date": "2026-07-23",
            "ai_assistance": "AI-assisted extraction and consistency checks; outcomes are fixed by an explicit conservative locator matrix.",
            "card_svg_rendered": f"docs/evidence_cards/{eid}.svg",
            "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
            "claim_boundary": row["target_statement"] + " This card is limited to one preregistered source boundary.",
            "claim_type": "source_boundary",
            "created_at": "2026-07-23",
            "domain": row["domain_slug"],
            "evidence_id": eid,
            "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json",
            "execution_mode": "AUTOMATED_AI_ASSISTED",
            "git_commit": "local-before-merge",
            "known_limitations": limitations,
            "last_verified_date": "2026-07-23",
            "manual_review": row["review_basis"] + f" Locator: {row['locator']}",
            "official_source_name": row["source_name"],
            "official_source_url": row["source_url"],
            "operator": args.operator,
            "protocol_id": row["claim_id"],
            "protocol_version": PROTOCOL,
            "raw_payload_committed": False,
            "raw_payload_manifest": f"HTTP {row['http_status']}; canonical {row['canonical_url']}; SHA-256 {row['source_sha256']}; source manifest {manifest_sha}; raw bytes retained locally only",
            "record_type": "source_audit",
            "registry_sequence": sequence,
            "reproduction_level": "not independently reproduced",
            "result_status": row["status"],
            "runner_command": "python scripts/claimbound_review_claim_batch_171.py --manifest <local> --raw-root <local> --meta-root <local> --text-root <local> --operator <handle>",
            "sanitized_report_path": str(REPORT.relative_to(ROOT)),
            "sanitized_report_sha256": report_sha,
            "source_rights_note": "Public documentation source; raw response bytes are not committed.",
            "verification_count": 1,
            "verification_level": "SINGLE_OPERATOR",
        }
        if row["status"] == "PASSED_UNDER_PROTOCOL":
            card["baseline_control_summary"] = f"Manual gate review passed only at verbatim locator: {row['locator']}"
        if row["status"] == "BLOCKED_SOURCE":
            card["block_reason"] = row["review_basis"]
        if row["status"] == "SOURCE_DRIFT":
            card["drift_reason"] = row["review_basis"]
        violations = validate_evidence_card(card)
        if violations:
            raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path = CARDS / f"{eid}.json"
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
        (CARDS / f"{eid}.svg").write_text(render_svg(path))
        new_entries.append(
            {
                **{k: card[k] for k in ("evidence_id", "registry_sequence", "result_status", "protocol_id", "domain", "record_type", "operator", "created_at", "last_verified_date", "verification_level", "verification_count", "reproduction_level", "official_source_name", "sanitized_report_path")},
                "path": str(path.relative_to(ROOT)),
            }
        )

    registry["cards"].extend(new_entries)
    registry["cards"].sort(key=lambda x: x["evidence_id"])
    registry["card_count"] = len(registry["cards"])
    registry["statistics"] = statistics(registry["cards"])
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"reviewed_cards": len(rows), "result_counts": counts, "registry_card_count": registry["card_count"], "report_sha256": report_sha}, indent=2))


if __name__ == "__main__":
    main()
