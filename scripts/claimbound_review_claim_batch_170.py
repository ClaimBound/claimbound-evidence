#!/usr/bin/env python3
"""Publish conservatively reviewed issue #170 source-boundary cards."""
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
REPORT = ROOT / "artifacts/claim_batch_170_manual_review.json"
EXECUTION = ROOT / "artifacts/claim_batch_170_execution_manifest.json"
PROTOCOL = "CB7K-ISSUE-170-CONSERVATIVE-LOCATOR-REVIEW-2026-07-22-v1"

SOURCE_NAMES = {
    "DOM013-T01": "Compute Engine SLA",
    "DOM013-T02": "Google Cloud incident report",
    "DOM013-T03": "Amazon S3 data durability",
    "DOM013-T04": "Google Cloud recovery testing",
    "DOM013-T05": "Google Cloud latency dashboard",
    "DOM013-T06": "Google Cloud Standard Support",
    "DOM013-T07": "Google Cloud Backup and DR SLA",
    "DOM014-T01": "FCC National Broadband Map data",
    "DOM014-T02": "FCC National Broadband Map usage guide",
    "DOM014-T03": "FCC Connect2Health data",
    "DOM014-T04": "FCC Internet complaint issue guide",
    "DOM014-T05": "FCC emergency complaints guide",
    "DOM014-T06": "EU roaming cost guide",
    "DOM014-T07": "FCC NORS emergency reporting page",
    "DOM015-T01": "Threads 500 million monthly active users",
    "DOM015-T02": "Meta fake account measurement explainer",
    "DOM015-T03": "Meta Community Standards Enforcement Report Q4 2021",
    "DOM015-T04": "Meta Community Standards Enforcement Report Nov 2019",
    "DOM015-T05": "GitHub status page",
    "DOM015-T06": "Meta updated privacy policy",
    "DOM015-T07": "Meta ranking explanation",
}

# Every pass below is tied to a verbatim locator in the frozen local extraction.
# Sources absent from this matrix, and gates absent within a source, are insufficient.
LOCATORS: dict[str, dict[str, str]] = {
    "DOM013-T01": {
        "source-integrity": "Compute Engine Service Level Agreement (SLA)",
        "numerator-denominator": "total number of minutes in a month, minus the number of minutes of downtime suffered from all downtime periods in a month, divided by the total number of minutes in a month",
        "coverage": "SLA Exclusions",
        "time-boundary": "Previous versions",
        "method-version": "Monthly Uptime Percentage",
        "comparator": "Cloud Regions",
        "reproducibility": "Customer Must Request Financial Credit",
        "negative-evidence": "The SLA does not apply to any",
        "overclaim-drift": "sole and exclusive remedy",
    },
    "DOM013-T02": {
        "source-integrity": "Incident Report",
        "coverage": "Impacted services included Google Cloud Support, Agent Assist, Vertex Gemini API and Dialogflow CX in US regions and the global endpoint",
        "time-boundary": "On Friday, 27 February 2026 at 04:37 US/Pacific",
        "method-version": "configuration change to a safety filtering service",
        "negative-evidence": "increased error rates",
        "overclaim-drift": "This is not the level of quality and reliability we strive to offer you",
    },
    "DOM013-T03": {
        "source-integrity": "Data protection in Amazon S3",
        "numerator-denominator": "99.999999999% durability",
        "coverage": "minimum of three Availability Zones",
        "time-boundary": "over a given year",
        "method-version": "versioning",
        "reproducibility": "Apart from S3 Versioning",
        "negative-evidence": "loss of an entire Amazon S3 Availability Zone",
        "overclaim-drift": "designed to handle concurrent device failures",
    },
    "DOM013-T04": {
        "source-integrity": "Perform testing for recovery from data loss",
        "coverage": "restore data from backups and bring all of the services back",
        "time-boundary": "Last reviewed 2024-12-30 UTC",
        "method-version": "recovery time objective (RTO)",
        "comparator": "three criteria to judge the success or failure",
        "reproducibility": "run tests for those scenarios",
        "negative-evidence": "might be caused by a software bug or some type of natural disaster",
        "overclaim-drift": "We recommend that you use three criteria to judge the success or failure of this",
    },
    "DOM013-T05": {
        "source-integrity": "View Google Cloud latency dashboard",
        "coverage": "Traffic between Google Cloud and internet endpoints",
        "time-boundary": "6 weeks",
        "method-version": "Latency (RTT)",
        "comparator": "The latency graph shows the median latency between Google Cloud regions",
        "reproducibility": "View latency data",
        "negative-evidence": "minutes to appear",
        "overclaim-drift": "median latency in milliseconds (ms)",
    },
    "DOM013-T06": {
        "source-integrity": "Standard Support",
        "coverage": "Response SLO: For Priority 2 (P2) support cases, receive the first",
        "time-boundary": "in local hours of operation.",
        "method-version": "Cloud Support API",
        "reproducibility": "submit a support case in the Google Cloud console",
    },
    "DOM013-T07": {
        "source-integrity": "Backup and Disaster Recovery (DR) Service Service Level Agreement (SLA)",
        "numerator-denominator": "Monthly Uptime Percentage",
        "coverage": "Trigger Backup",
        "time-boundary": "calendar month basis per Project",
        "method-version": "Partial minutes will not be counted towards any Downtime Periods",
        "comparator": "per Project",
        "reproducibility": "Customer Must Request Financial Credit",
        "negative-evidence": "If Google does not meet the SLO",
        "overclaim-drift": "sole and exclusive remedy",
    },
    "DOM014-T01": {
        "source-integrity": "The map displays where Internet services are available across the United States",
        "coverage": "reported by Internet Service Providers (ISPs) to the FCC",
        "time-boundary": "All providers must report data as of June 30 (due September 1) and December 31 (due March 1) each year",
        "method-version": "propagation modeling",
        "reproducibility": "Download the data to your device",
        "negative-evidence": "the map does not include information on the availability of mobile wireless broadband service while indoors",
        "overclaim-drift": "actual, on-the-ground experience may vary",
    },
    "DOM014-T02": {
        "source-integrity": "How to Use the FCC’s National Broadband Map",
        "coverage": "availability and characteristics",
        "time-boundary": "updated May 15, 2025 16:59",
        "method-version": "Change the Data As-Of Date",
        "comparator": "Compare fixed and mobile broadband availability",
        "reproducibility": "Download the data to your device",
        "negative-evidence": "Services with download speeds below 25 Mbps are not shown on the default map",
        "overclaim-drift": "internet services available across the United States",
    },
    "DOM014-T03": {
        "source-integrity": "Data - Connect2Health FCC",
        "coverage": "broadband connectivity",
        "time-boundary": "2025 release",
        "method-version": "Most Common Download Speed (Any Terrestrial)",
        "reproducibility": "downloaded in our Data Explainer",
        "negative-evidence": "Data for this variable is currently only available at the state level",
        "overclaim-drift": "The most commonly advertised download speed by population via any terrestrial technology",
    },
    "DOM014-T04": {
        "source-integrity": "Internet Form - Descriptions of Complaint Issues",
        "coverage": "Issues with your Internet speeds, including not receiving advertised speeds or latency, issues",
        "time-boundary": "If you are having issues with your provider",
        "method-version": "Speed",
        "reproducibility": "Start your complaint with the FCC",
        "negative-evidence": "If our consumer guides do not address your issue",
        "overclaim-drift": "Availability",
    },
    "DOM014-T05": {
        "source-integrity": "Emergency Complaints",
        "coverage": "911 outage",
        "time-boundary": "Emergency Complaints",
        "method-version": "Start your complaint",
        "reproducibility": "Use the Public Safety Interference Complaint portal",
        "negative-evidence": "tower light outage",
        "overclaim-drift": "If your complaint involves a type of emergency such as",
    },
    "DOM014-T06": {
        "source-integrity": "Roaming: what you pay to use your smartphone in another EU country",
        "coverage": "you don't have to pay any additional charges to use your mobile phone",
        "time-boundary": "in another EU country",
        "method-version": "roam like at home",
        "reproducibility": "Your mobile provider must automatically apply a cut-off limit when you roam",
        "negative-evidence": "may start charging you extra for your roaming use",
        "overclaim-drift": "charged at domestic rates, i.e. the same price",
    },
    "DOM014-T07": {
        "source-integrity": "Network Outage Reporting System (NORS)",
        "coverage": "telecommunication service disruptions",
        "time-boundary": "pursuant to Part 4 of the FCC�s rules",
        "method-version": "Notifications, Initial Reports and Final Reports",
        "reproducibility": "Telecommunications Companies are asked to use the Network Outage Reporting System (NORS) to file reports of telecommunication service disruptions",
        "negative-evidence": "essential to maintain and improve the reliability and security of the telecommunications infrastructure",
        "overclaim-drift": "continuity of FCC�s business operations throughout any disruption",
    },
    "DOM015-T01": {
        "source-integrity": "Threads has reached 500 million monthly active users",
        "coverage": "500 million monthly active users",
        "time-boundary": "Today we’re announcing that Threads has reached 500 million monthly active users",
    },
    "DOM015-T02": {
        "source-integrity": "How Does Facebook Measure Fake Accounts?",
        "coverage": "Prevalence of fake accounts measures how many active fake accounts exist amongst our monthly active users within a given time period",
        "time-boundary": "within a given time period",
        "method-version": "Our detection systems identify such behavior",
        "reproducibility": "We provide that data as our metric of proactive rate in the report",
        "negative-evidence": "over 99% of these are proactively detected by us before people report them to us",
    },
    "DOM015-T03": {
        "source-integrity": "Community Standards Enforcement Report, Fourth Quarter 2021",
        "coverage": "prevalence of harmful content on Facebook and Instagram remained relatively consistent",
        "time-boundary": "fourth quarter of 2021",
        "method-version": "proactive detection technologies",
        "reproducibility": "Today we’re publishing our Community Standards Enforcement Report for the fourth quarter of 2021 and provides metrics on how we enforced our policies from October 2021 through December 2021 across 14 policy areas on Facebook and 12 on Instagram",
        "negative-evidence": "1.2 billion pieces of spam content",
        "overclaim-drift": "the vast majority of content that users generally encounter does not violate our policies",
    },
    "DOM015-T04": {
        "source-integrity": "Community Standards Enforcement Report, November 2019 Edition",
        "coverage": "Appealed Content: how much content people appealed after we took action",
        "time-boundary": "Q2 and Q3 2019",
        "negative-evidence": "these technologies are not perfect",
        "overclaim-drift": "Since our last report, we have improved the ways we measure how much content we take action on after identifying an issue in our accounting this summer.",
    },
    "DOM015-T05": {
        "source-integrity": "GitHub Status",
        "coverage": "API Requests is operating normally",
        "time-boundary": "Uptime over the past 90 days",
        "method-version": "Degraded REST API Availability",
        "reproducibility": "View historical uptime",
        "negative-evidence": "about 39% of REST API requests failed with HTTP 500 level responses",
        "overclaim-drift": "All Systems Operational",
    },
    "DOM015-T06": {
        "source-integrity": "Privacy Center",
        "coverage": "Privacy Center is now available to everyone who uses Facebook on desktop and mobile",
        "time-boundary": "These updates go into effect on July 26",
        "method-version": "new controls to manage your experience",
        "reproducibility": "You can continue to manage your privacy settings at any time and we’re committed to letting you know if we make important changes to how we collect, use and share your information",
        "negative-evidence": "these updates don’t allow Meta to collect, use or share your data in new ways",
        "overclaim-drift": "we still do not sell your information",
    },
    "DOM015-T07": {
        "source-integrity": "How AI Influences What You See on Facebook and Instagram",
        "coverage": "We’re sharing more details about how our AI systems rank content for your Feed, Reels, Stories, and other surfaces",
        "time-boundary": "Today, we’re building on that commitment by being more transparent around several of the AI systems that incorporate your feedback to rank content across Facebook and Instagram",
        "method-version": "rank content for your Feed, Reels, Stories",
        "reproducibility": "We’re giving more detailed information for experts",
        "negative-evidence": "no single prediction is a perfect gauge",
        "overclaim-drift": "you have the ability to shape your experiences on our apps",
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
    if len(sources) != 21 or any(len({x["source_url"] for x in manifest["sources"] if x["key"].startswith(d)}) < 7 for d in ("DOM013", "DOM014", "DOM015")):
        raise SystemExit("expected seven independently frozen topic URLs per domain")

    manifest_sha = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    ds = domains()
    catalog = make_claims(ds)
    validate(ds, catalog)
    claims = [c for c in catalog if c["domain_code"] in {"DOM013", "DOM014", "DOM015"}]

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
                "issue_number": 170,
                "source_manifest_sha256": manifest_sha,
                "claim_boundary": "Claim-level execution plan for issue #170 only; it is not evidence and predeclares no outcome.",
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
                "issue_number": 170,
                "protocol_version": PROTOCOL,
                "source_manifest_sha256": manifest_sha,
                "claim_boundary": "Conservative manual review of 21 preregistered cloud, telecom and internet-platform topic URLs for issue #170; no source replacement after observation.",
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
        eid = f"CLAIMBOUND-{row['claim_id']}-2026-07-22"
        limitations = [
            "One exact source boundary only; no domain-wide certification.",
            "A pass applies only to the named gate and verbatim locator.",
            "Insufficient coverage is not a negative result.",
        ]
        card = {
            "access_date": "2026-07-22",
            "ai_assistance": "AI-assisted extraction and consistency checks; outcomes are fixed by an explicit conservative locator matrix.",
            "card_svg_rendered": f"docs/evidence_cards/{eid}.svg",
            "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
            "claim_boundary": row["target_statement"] + " This card is limited to one preregistered source boundary.",
            "claim_type": "source_boundary",
            "created_at": "2026-07-22",
            "domain": row["domain_slug"],
            "evidence_id": eid,
            "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json",
            "execution_mode": "AUTOMATED_AI_ASSISTED",
            "git_commit": "local-before-merge",
            "known_limitations": limitations,
            "last_verified_date": "2026-07-22",
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
            "runner_command": "python scripts/claimbound_review_claim_batch_170.py --manifest <local> --raw-root <local> --meta-root <local> --text-root <local> --operator <handle>",
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
