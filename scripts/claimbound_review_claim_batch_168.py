#!/usr/bin/env python3
"""Publish conservatively reviewed issue #168 source-boundary cards."""
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
REPORT = ROOT / "artifacts/claim_batch_168_manual_review.json"
EXECUTION = ROOT / "artifacts/claim_batch_168_execution_manifest.json"
PROTOCOL = "CB7K-ISSUE-168-CONSERVATIVE-LOCATOR-REVIEW-2026-07-22-v1"

SOURCE_NAMES = {
    "DOM007-T01": "NIST ARIAC scoring documentation", "DOM007-T02": "NIST ARIAC runtime-verification paper",
    "DOM007-T03": "NIST ARIAC prize spotlight", "DOM007-T04": "NIST UAS payload challenge page",
    "DOM007-T05": "NIST Robotics program", "DOM007-T06": "NIST ARIAC competition page",
    "DOM007-T07": "NIST Agility Performance of Robotic Systems",
    "DOM008-T01": "NIST FRTE 1:N Identification", "DOM008-T02": "NIST FRTE 1:1 Verification",
    "DOM008-T03": "NIST FRVT Part 3 Demographic Effects", "DOM008-T04": "NIST FRTE 1:N Performance section",
    "DOM008-T05": "NIST FATE Quality", "DOM008-T06": "NIST FRTE 1:1 draft report",
    "DOM008-T07": "NIST FRTE program page",
    "DOM009-T01": "NIST SP 800-63A-4 IAL requirements", "DOM009-T02": "NIST SP 800-63A-4 identity resolution section",
    "DOM009-T03": "NIST SP 800-63B-4 account recovery section", "DOM009-T04": "NIST SP 800-63A-4 verification section",
    "DOM009-T05": "NIST SP 800-63A-4 security considerations", "DOM009-T06": "NIST SP 800-63A-4 customer experience",
    "DOM009-T07": "NIST SP 800-63A-4 privacy considerations",
}

# Every pass below is tied to a verbatim locator in the frozen local extraction.
# Sources absent from this matrix, and gates absent within a source, are insufficient.
LOCATORS: dict[str, dict[str, str]] = {
    "DOM007-T01": {
        "source-integrity": "This page describes the scoring system for the competition.",
        "numerator-denominator": "aggregated into an execution score (80%) and combined with human judging (20%)",
        "coverage": "across multiple runs and trials",
        "method-version": "scores calculated based on task completion, efficiency bonuses, and penalty deductions",
        "negative-evidence": "The exact penalty values are subject to change",
        "overclaim-drift": "The exact penalty values are subject to change",
    },
    "DOM007-T02": {
        "source-integrity": "Runtime Verification of the ARIAC competition: Can a",
        "method-version": "ARIAC comes with a set of score metrics to evaluate",
        "negative-evidence": "Figure 2: Robot about to collide with a human.",
        "conflicts-disclosure": "zeid.kootbally@nist.gov",
    },
    "DOM007-T07": {
        "source-integrity": "Agility Performance of Robotic Systems | NIST",
        "coverage": "applied to industry-relevant scenarios",
        "time-boundary": "Updated April 24, 2026",
        "method-version": "Robot agility test methods and performance metrics will be exercised and will be validated through",
        "reproducibility": "make the Robot Agility Lab available to the public as a testbed",
        "overclaim-drift": "These proof-of-concept implementations",
    },
    "DOM008-T01": {
        "source-integrity": "Face Recognition Technology Evaluation (FRTE) 1:N Identification",
        "numerator-denominator": "FPIR is the proportion of non-mated searches producing one or more candidates above threshold.",
        "coverage": "the number of persons in the gallery",
        "time-boundary": "[last updated: 2026-07-08]",
        "method-version": "The threshold is set for each algorithm and each column separately.",
        "negative-evidence": "Such outcomes have application-dependent consequences, which can be serious.",
        "overclaim-drift": "The duration values for algorithms submitted since 2025-09-04 are provisional.",
    },
    "DOM008-T02": {
        "source-integrity": "Face Recognition Technology Evaluation (FRTE) 1:1 Verification",
        "numerator-denominator": "FNMR is the proportion of mated comparisons below a threshold set to achieve the false match rate (FMR) specified.",
        "coverage": "NIST included all algorithms evaluated since the ongoing FRTE evaluation started in 2017.",
        "time-boundary": "[last updated: 2026-06-15]",
        "method-version": "Algorithms submitted to FRTE implement NIST’s application programming interface (API).",
        "negative-evidence": "may be revised after the conclusion of our investigation",
        "overclaim-drift": "It is a draft made available for comments.",
    },
    "DOM008-T03": {
        "source-integrity": "Face Recognition Vendor Test Part 3: Demographic Effects",
        "time-boundary": "(2019), Face Recognition Vendor Test Part 3: Demographic Effects",
        "conflicts-disclosure": "National Institute of Standards and Technology, Gaithersburg, MD",
    },
    "DOM008-T04": {
        "source-integrity": "Face Recognition Technology Evaluation (FRTE) 1:N Identification",
        "coverage": "the number of persons in the gallery",
        "method-version": "the algorithm returns a fixed number (50) of candidates",
        "negative-evidence": "the reviewer must reject all the candidates",
    },
    "DOM008-T05": {
        "source-integrity": "Face Analysis Technology Evaluation (FATE) Quality",
        "numerator-denominator": "after discarding one and five percent of the lowest quality samples",
        "coverage": "non-ideal pose, illumination and resolution",
        "method-version": "We set a recognition threshold such that the false non-match rate (FNMR) from a set of 15 accurate FRTE verification algorithms is 1%.",
        "negative-evidence": "the QAA does not always assign low quality values to images involved in false non-matches.",
        "overclaim-drift": "the QAA does not always assign low quality values to images involved in false non-matches.",
    },
    "DOM008-T06": {
        "source-integrity": "NISTIR XXXX Draft",
        "negative-evidence": "This report is a draft NIST Interagency Report, and is open for comment.",
        "overclaim-drift": "This report is a draft NIST Interagency Report, and is open for comment.",
    },
    "DOM009-T01": {
        "source-integrity": "Identity Proofing Requirements",
        "coverage": "identity proofing processes at IAL1",
        "method-version": "be validated using one of the following methods:",
        "negative-evidence": "minimizing the rejection of legitimate users",
        "overclaim-drift": "The use of biometric matching",
    },
    "DOM009-T05": {
        "source-integrity": "Threats and Security Considerations",
        "coverage": "There are four general categories of threats",
        "method-version": "Threat Mitigation Strategies",
        "negative-evidence": "False or fraudulent representation",
        "overclaim-drift": "These mitigations should not be considered comprehensive",
    },
    "DOM009-T06": {
        "source-integrity": "Customer Experience Considerations",
        "coverage": "representative users, realistic goals and tasks, and appropriate contexts of use",
        "method-version": "An effective usability evaluation",
        "negative-evidence": "users who may have failed remote or automated approaches through no fault of their own",
        "overclaim-drift": "This section is intended to raise implementers’ awareness",
    },
    "DOM009-T07": {
        "source-integrity": "Privacy Considerations",
        "coverage": "only the personal information necessary to validate the claimed identity",
        "method-version": "subject to a privacy risk assessment",
        "negative-evidence": "retention of personal information can become vulnerable to unauthorized access or use",
        "overclaim-drift": "Where possible, CSPs and agencies should consider mechanisms",
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
    return {name: dict(sorted(Counter(x[field] for x in entries).items())) for name, field in (
        ("by_domain", "domain"), ("by_record_type", "record_type"),
        ("by_result_status", "result_status"), ("by_source", "official_source_name"))}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--raw-root", type=Path, required=True)
    p.add_argument("--meta-root", type=Path, required=True); p.add_argument("--text-root", type=Path, required=True)
    p.add_argument("--operator", required=True); args = p.parse_args()
    manifest = json.loads(args.manifest.read_text()); sources = {x["key"]: x for x in manifest["sources"]}
    if len(sources) != 21 or any(len({x["source_url"] for x in manifest["sources"] if x["key"].startswith(d)}) < 7 for d in ("DOM007", "DOM008", "DOM009")):
        raise SystemExit("expected seven independently frozen topic URLs per domain")
    manifest_sha = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    ds = domains(); catalog = make_claims(ds); validate(ds, catalog)
    claims = [c for c in catalog if c["domain_code"] in {"DOM007", "DOM008", "DOM009"}]
    source_rows = {}
    for key, source in sources.items():
        raw = args.raw_root / f"{key}.bin"; meta = json.loads((args.meta_root / f"{key}.json").read_text())
        source_rows[key] = {**source, **meta, "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "text": (args.text_root / f"{key}.txt").read_text(errors="replace")}
    execution, rows = [], []
    for claim in claims:
        key = source_key(claim); source = source_rows[key]; gate = claim["gate"]; target = GATE_TARGETS[gate].format(topic=claim["topic"])
        execution.append({"claim_id": claim["claim_id"], "source_url": source["source_url"], "evaluation_method": GATE_METHODS[gate], "frozen_parameters": {"topic": claim["topic"], "gate": gate}, "support_rule": target, "negative_rule": claim["adjudication_rule"]})
        if source["http_status"] != 200:
            decision = {"status": "BLOCKED_SOURCE", "locator": f"HTTP {source['http_status']}", "review_basis": "The exact preregistered URL was inaccessible; no replacement was selected."}
        elif source["final_url"] != source["source_url"]:
            decision = {"status": "SOURCE_DRIFT", "locator": f"selected={source['source_url']} canonical={source['final_url']}", "review_basis": "The frozen URL resolved outside its selected source boundary."}
        elif key in LOCATORS and gate in LOCATORS[key]:
            locator = LOCATORS[key][gate]
            if locator.casefold() not in source["text"].casefold(): raise SystemExit(f"{claim['claim_id']}: absent locator {locator!r}")
            decision = {"status": "PASSED_UNDER_PROTOCOL", "locator": locator, "review_basis": "Manual conservative review found the required disclosure at this verbatim locator."}
        else:
            locator = LOCATORS.get(key, {}).get("source-integrity", (source["text"].splitlines() or ["empty extraction"])[0])
            decision = {"status": "INSUFFICIENT_COVERAGE", "locator": locator, "review_basis": "The frozen source was reviewed but did not expose complete gate-specific evidence; absence was not converted into a negative result."}
        rows.append({**claim, **decision, "target_statement": target, "source_name": SOURCE_NAMES[key], "source_url": source["source_url"], "canonical_url": source["final_url"], "http_status": source["http_status"], "source_sha256": source["sha256"]})
    EXECUTION.write_text(json.dumps({"issue_number": 168, "source_manifest_sha256": manifest_sha, "claim_boundary": "Claim-level execution plan for issue #168 only; it is not evidence and predeclares no outcome.", "raw_payload_committed": False, "entries": execution}, indent=2, ensure_ascii=False) + "\n")
    counts = dict(Counter(x["status"] for x in rows))
    REPORT.write_text(json.dumps({"issue_number": 168, "protocol_version": PROTOCOL, "source_manifest_sha256": manifest_sha, "claim_boundary": "Conservative manual review of 21 preregistered NIST topic URLs for issue #168; no source replacement after observation.", "operator": args.operator, "raw_payload_committed": False, "review_method": "explicit gate-to-verbatim-locator matrix; unreviewed or incomplete gates remain insufficient", "result_counts": counts, "cards": rows}, indent=2, ensure_ascii=False) + "\n")
    report_sha = hashlib.sha256(REPORT.read_bytes()).hexdigest(); registry = json.loads(REGISTRY.read_text()); sequence = max(x["registry_sequence"] for x in registry["cards"]); new_entries = []
    for row in rows:
        sequence += 1; eid = f"CLAIMBOUND-{row['claim_id']}-2026-07-22"
        limitations = ["One exact source boundary only; no domain-wide certification.", "A pass applies only to the named gate and verbatim locator.", "Insufficient coverage is not a negative result."]
        if row["claim_id"].startswith("CB7K-DOM008-T06-"): limitations.append("The 1054-page PDF raw file is complete, but local text review was limited to its first 50 pages.")
        card = {"access_date": "2026-07-22", "ai_assistance": "AI-assisted extraction and consistency checks; outcomes are fixed by an explicit conservative locator matrix.", "card_svg_rendered": f"docs/evidence_cards/{eid}.svg", "card_svg_template": "docs/assets/claimbound_evidence_card.svg", "claim_boundary": row["target_statement"] + " This card is limited to one preregistered source boundary.", "claim_type": "source_boundary", "created_at": "2026-07-22", "domain": row["domain_slug"], "evidence_id": eid, "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json", "execution_mode": "AUTOMATED_AI_ASSISTED", "git_commit": "local-before-merge", "known_limitations": limitations, "last_verified_date": "2026-07-22", "manual_review": row["review_basis"] + f" Locator: {row['locator']}", "official_source_name": row["source_name"], "official_source_url": row["source_url"], "operator": args.operator, "protocol_id": row["claim_id"], "protocol_version": PROTOCOL, "raw_payload_committed": False, "raw_payload_manifest": f"HTTP {row['http_status']}; canonical {row['canonical_url']}; SHA-256 {row['source_sha256']}; source manifest {manifest_sha}; raw bytes retained locally only", "record_type": "source_audit", "registry_sequence": sequence, "reproduction_level": "not independently reproduced", "result_status": row["status"], "runner_command": "python scripts/claimbound_review_claim_batch_168.py --manifest <local> --raw-root <local> --meta-root <local> --text-root <local> --operator <handle>", "sanitized_report_path": str(REPORT.relative_to(ROOT)), "sanitized_report_sha256": report_sha, "source_rights_note": "NIST public source; raw response bytes are not committed.", "verification_count": 1, "verification_level": "SINGLE_OPERATOR"}
        if row["status"] == "PASSED_UNDER_PROTOCOL": card["baseline_control_summary"] = f"Manual gate review passed only at verbatim locator: {row['locator']}"
        if row["status"] == "BLOCKED_SOURCE": card["block_reason"] = row["review_basis"]
        if row["status"] == "SOURCE_DRIFT": card["drift_reason"] = row["review_basis"]
        violations = validate_evidence_card(card)
        if violations: raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path = CARDS / f"{eid}.json"; path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n"); (CARDS / f"{eid}.svg").write_text(render_svg(path))
        new_entries.append({k: card[k] for k in ("evidence_id", "registry_sequence", "result_status", "protocol_id", "domain", "record_type", "operator", "created_at", "last_verified_date", "verification_level", "verification_count", "reproduction_level", "official_source_name", "sanitized_report_path")} | {"path": str(path.relative_to(ROOT))})
    registry["cards"].extend(new_entries); registry["cards"].sort(key=lambda x: x["evidence_id"]); registry["card_count"] = len(registry["cards"]); registry["statistics"] = statistics(registry["cards"]); REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"reviewed_cards": len(rows), "result_counts": counts, "registry_card_count": registry["card_count"], "report_sha256": report_sha}, indent=2))

if __name__ == "__main__": main()
