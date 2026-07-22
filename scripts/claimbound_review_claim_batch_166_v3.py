#!/usr/bin/env python3
"""Manually adjudicate issue #166 from the already-frozen v2 source bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from build_public_claim_catalog import domains, make_claims, validate
from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs/evidence_cards"
REGISTRY = ROOT / "docs/registry/evidence_index.json"
V2_REPORT = ROOT / "artifacts/claim_batch_166_v2_summary.json"
V3_REPORT = ROOT / "artifacts/claim_batch_166_v3_manual_review.json"
PROTOCOL = "CB7K-ISSUE-166-MANUAL-SECTION-REVIEW-2026-07-20-v3"

GATE_TARGETS = {
    "source-integrity": "The frozen bytes identify an exact official source and a topic-specific section for {topic}.",
    "numerator-denominator": "One frozen numeric result for {topic} discloses its numerator, denominator, units, exclusions, and rounding rule.",
    "coverage": "The source states the evaluated population, task scope, exclusions, or limitations for {topic}.",
    "time-boundary": "The source fixes a publication or update date and model or benchmark version for {topic}.",
    "method-version": "The source identifies the method or evaluation procedure and its applicable version for {topic}.",
    "comparator": "The source identifies a comparable baseline and measurement rule for {topic}.",
    "reproducibility": "A public operator can obtain the disclosed inputs and rerun the frozen {topic} procedure without private material.",
    "negative-evidence": "The selected boundary explicitly includes limitations, failures, adverse evidence, or contradictory results relevant to {topic}.",
    "conflicts-disclosure": "The selected boundary identifies the vendor, author, sponsor, or institutional interest responsible for the {topic} report.",
    "overclaim-drift": "The source contains an explicit caveat preventing the {topic} result from becoming a universal guarantee.",
}

# These decisions were reviewed against exact local text extracted from the frozen
# payload hashes. A PASS is allowed only when its locator occurs verbatim in that
# topic payload. Outcomes are data, not inferred by token-counting code.
FULL_REVIEWS: dict[tuple[str, int], dict[str, str]] = {
    ("DOM001", 2): {
        "topic": "Production Benchmarks with Challenging Prompts",
        "date": "Published April 23, 2026",
        "scope": "evaluations represent a lower bound for potential capabilities",
        "method": "methods, including scaffolding and prompting where relevant",
        "comparator": "Table 1. Production Benchmarks with Challenging Prompts",
        "negative": "evaluations represent a lower bound for potential capabilities",
        "vendor": "OpenAI Deployment Safety Hub",
        "caveat": "evaluations represent a lower bound for potential capabilities",
    },
    ("DOM001", 6): {
        "topic": "Model Safety Training and Evaluation",
        "date": "Published July 9, 2026",
        "scope": "limitations to these evaluations",
        "method": "methods, including scaffolding and prompting where relevant",
        "comparator": "Table 1",
        "negative": "limitations to these evaluations",
        "vendor": "OpenAI Deployment Safety Hub",
        "caveat": "evaluations represent a lower bound for potential capabilities",
    },
    ("DOM003", 1): {
        "topic": "Capabilities Assessment",
        "date": "Published July 9, 2026",
        "scope": "limitations to these evaluations",
        "method": "methods, including scaffolding and prompting where relevant",
        "comparator": "Table 13",
        "negative": "limitations to these evaluations",
        "vendor": "OpenAI Deployment Safety Hub",
        "caveat": "evaluations represent a lower bound for potential capabilities",
    },
    ("DOM003", 3): {
        "topic": "Long-form Biological Risk Questions",
        "date": "Published August 7, 2025",
        "scope": "evaluations represent a lower bound for potential capabilities",
        "method": "methods, including custom post-training",
        "comparator": "median domain expert baseline",
        "negative": "lower bounds on model capability",
        "vendor": "OpenAI Deployment Safety Hub",
        "caveat": "lower bounds on model capability",
    },
    ("DOM003", 4): {
        "topic": "6.1.2 Cybersecurity",
        "date": "Published August 7, 2025",
        "scope": "evaluations represent a lower bound for potential capabilities",
        "method": "methods, including custom post-training",
        "comparator": "Table 16",
        "negative": "failures reflect real capability limitations",
        "vendor": "OpenAI Deployment Safety Hub",
        "caveat": "lower bounds on model capability",
    },
    ("DOM003", 6): {
        "topic": "Standard refusal evaluation",
        "date": "Published March 1, 2024",
        "scope": "other limitations contributed",
        "method": "Standard Refusal Evaluation",
        "comparator": "Table 1. Standard refusal evaluation",
        "negative": "other limitations contributed",
        "vendor": "OpenAI Deployment Safety Hub",
        "caveat": "other limitations contributed",
    },
}

PARTIAL_REVIEWS: dict[tuple[str, int], dict[str, str]] = {
    ("DOM001", 1): {
        "topic": "2. Model Data and Training",
        "date": "Published July 9, 2026",
        "vendor": "OpenAI Deployment Safety Hub",
    }
}

BLOCKED = {("DOM001", 3), ("DOM001", 4), ("DOM001", 7), ("DOM003", 2)}
DRIFT = {("DOM001", 5)}
SHELL_ONLY = {("DOM002", i) for i in range(1, 8)}
TOPIC_MISMATCH = {("DOM003", 5), ("DOM003", 7)}

PASS_LOCATOR_BY_GATE = {
    "source-integrity": "topic",
    "coverage": "scope",
    "time-boundary": "date",
    "method-version": "method",
    "comparator": "comparator",
    "negative-evidence": "negative",
    "conflicts-disclosure": "vendor",
    "overclaim-drift": "caveat",
}


def extracted_texts(path: Path) -> dict[tuple[str, int], str]:
    result = {}
    for domain in ("DOM001", "DOM002", "DOM003"):
        for topic in range(1, 8):
            p = path / f"{domain}-T{topic:02d}.txt"
            if not p.is_file():
                raise SystemExit(f"missing reviewed text: {p}")
            result[(domain, topic)] = p.read_text(encoding="utf-8")
    return result


def source_rows() -> dict[tuple[str, int], dict[str, Any]]:
    report = json.loads(V2_REPORT.read_text(encoding="utf-8"))
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in report["cards"]:
        rows.setdefault((row["domain_code"], row["topic_index"]), row)
    if len(rows) != 21:
        raise SystemExit(f"expected 21 frozen topic sources, got {len(rows)}")
    return rows


def verify_raw(raw_root: Path, rows: dict[tuple[str, int], dict[str, Any]]) -> None:
    for key, row in rows.items():
        path = raw_root / f"{key[0]}-T{key[1]:02d}.bin"
        if not path.is_file():
            raise SystemExit(f"missing frozen payload: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            raise SystemExit(f"{path}: SHA-256 differs from frozen report")


def decision(claim: dict[str, Any], source: dict[str, Any], text: str) -> dict[str, str]:
    key = (claim["domain_code"], claim["topic_index"])
    gate = claim["gate"]
    target = GATE_TARGETS[gate].format(topic=claim["topic"])
    if key in BLOCKED:
        return {"status": "BLOCKED_SOURCE", "target_statement": target, "locator": f"HTTP {source['http_status']}", "review_basis": "The exact frozen URL returned HTTP 403; no substitute source was selected."}
    if key in DRIFT:
        return {"status": "SOURCE_DRIFT", "target_statement": target, "locator": f"selected={source['source_url']} canonical={source['canonical_url']}", "review_basis": "The frozen reports URL redirected to the generic stories boundary before claim adjudication."}
    if key in SHELL_ONLY:
        return {"status": "INSUFFICIENT_COVERAGE", "target_statement": target, "locator": "Holistic Evaluation of Language Models (HELM)", "review_basis": "The frozen response contains only the HELM application shell title and no topic-specific specification, table, method, or result."}
    if key in TOPIC_MISMATCH:
        return {"status": "INSUFFICIENT_COVERAGE", "target_statement": target, "locator": "source title and table of contents manually reviewed", "review_basis": f"The frozen source does not adjudicate the selected topic '{claim['topic']}'; a nearby capability or deployment discussion is not a substitute."}
    review = FULL_REVIEWS.get(key)
    if review is not None:
        locator_key = PASS_LOCATOR_BY_GATE.get(gate)
        if locator_key is not None:
            locator = review[locator_key]
            if locator.lower() not in text.lower():
                raise SystemExit(f"{claim['claim_id']}: reviewed locator absent: {locator!r}")
            return {"status": "PASSED_UNDER_PROTOCOL", "target_statement": target, "locator": locator, "review_basis": f"Manual section review found the gate-specific disclosure at locator: {locator}."}
        missing = "raw numerator/denominator and rounding inputs" if gate == "numerator-denominator" else "public executable inputs and a complete rerun recipe"
        return {"status": "INSUFFICIENT_COVERAGE", "target_statement": target, "locator": review["topic"], "review_basis": f"The relevant section was reviewed, but it does not disclose {missing}."}
    review = PARTIAL_REVIEWS.get(key)
    if review is not None and gate in {"source-integrity", "time-boundary", "conflicts-disclosure"}:
        locator = review[{"source-integrity": "topic", "time-boundary": "date", "conflicts-disclosure": "vendor"}[gate]]
        if locator.lower() not in text.lower():
            raise SystemExit(f"{claim['claim_id']}: reviewed locator absent: {locator!r}")
        return {"status": "PASSED_UNDER_PROTOCOL", "target_statement": target, "locator": locator, "review_basis": f"Manual review found this narrow disclosure at locator: {locator}."}
    if review is not None:
        return {"status": "INSUFFICIENT_COVERAGE", "target_statement": target, "locator": review["topic"], "review_basis": "The training-data paragraph was reviewed; it names only broad dataset categories and does not disclose the gate-specific population, method, comparator, rerun inputs, adverse register, or caveat required here."}
    raise SystemExit(f"no manual topic review for {key}")


def registry_entry(card: dict[str, Any], path: Path) -> dict[str, Any]:
    keys = ("evidence_id", "registry_sequence", "result_status", "protocol_id", "domain", "record_type", "operator", "created_at", "last_verified_date", "verification_level", "verification_count", "reproduction_level", "official_source_name", "sanitized_report_path")
    return {k: card[k] for k in keys} | {"path": str(path.relative_to(ROOT))}


def statistics(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "by_domain": dict(sorted(Counter(x["domain"] for x in entries).items())),
        "by_record_type": dict(sorted(Counter(x["record_type"] for x in entries).items())),
        "by_result_status": dict(sorted(Counter(x["result_status"] for x in entries).items())),
        "by_source": dict(sorted(Counter(x["official_source_name"] for x in entries).items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--text-root", type=Path, required=True)
    parser.add_argument("--operator", required=True)
    args = parser.parse_args()
    sources = source_rows()
    verify_raw(args.raw_root, sources)
    texts = extracted_texts(args.text_root)
    ds = domains(); all_claims = make_claims(ds); validate(ds, all_claims)
    claims = [c for c in all_claims if c["domain_code"] in {"DOM001", "DOM002", "DOM003"}]
    rows = []
    for claim in claims:
        key = (claim["domain_code"], claim["topic_index"])
        rows.append({**claim, **decision(claim, sources[key], texts[key]), "source_name": sources[key]["source_name"], "source_url": sources[key]["source_url"], "canonical_url": sources[key]["canonical_url"], "http_status": sources[key]["http_status"], "source_sha256": sources[key]["sha256"]})
    if len(rows) != 210 or len({x["claim_id"] for x in rows}) != 210:
        raise SystemExit("manual review must contain 210 unique claims")
    counts = dict(Counter(x["status"] for x in rows))
    report = {"issue_number": 166, "protocol_version": PROTOCOL, "claim_boundary": "Manual section/field review of the original 21 frozen topic sources for all 210 issue #166 candidates; no source was replaced after observation.", "operator": args.operator, "raw_payload_committed": False, "review_method": "explicit topic-by-gate decision matrix with verbatim locators; no bag-of-words outcome assignment", "result_counts": counts, "cards": rows}
    V3_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_sha = hashlib.sha256(V3_REPORT.read_bytes()).hexdigest()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    reg_by_protocol = {x["protocol_id"]: x for x in registry["cards"]}
    new_entries = []
    for row in rows:
        existing = reg_by_protocol.get(row["claim_id"])
        if existing is None:
            raise SystemExit(f"missing existing v2 registry entry: {row['claim_id']}")
        eid = existing["evidence_id"]
        card = {
            "access_date": "2026-07-20", "ai_assistance": "AI assisted extraction and consistency checks; every outcome is fixed by the explicit manual topic-by-gate review matrix.",
            "card_svg_rendered": f"docs/evidence_cards/{eid}.svg", "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
            "claim_boundary": row["target_statement"] + " This card is limited to the original frozen source boundary.", "claim_type": "source_boundary", "created_at": "2026-07-20", "domain": row["domain_slug"], "evidence_id": eid,
            "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json", "execution_mode": "AUTOMATED_AI_ASSISTED", "git_commit": "local-corrective-review",
            "known_limitations": ["One exact frozen source boundary only; no domain-wide certification.", "A pass applies only to the named gate and locator.", "Insufficient coverage is not a negative result."], "last_verified_date": "2026-07-20",
            "manual_review": row["review_basis"] + f" Locator: {row['locator']}", "official_source_name": row["source_name"], "official_source_url": row["source_url"], "operator": args.operator,
            "protocol_id": row["claim_id"], "protocol_version": PROTOCOL, "raw_payload_committed": False,
            "raw_payload_manifest": f"HTTP {row['http_status']}; canonical {row['canonical_url']}; frozen response SHA-256 {row['source_sha256']}; raw bytes retained outside the repository",
            "record_type": "source_audit", "registry_sequence": existing["registry_sequence"], "reproduction_level": "not independently reproduced", "result_status": row["status"],
            "runner_command": "python scripts/claimbound_review_claim_batch_166_v3.py --raw-root <local> --text-root <local> --operator <handle>",
            "sanitized_report_path": str(V3_REPORT.relative_to(ROOT)), "sanitized_report_sha256": report_sha, "source_rights_note": "Official public source; raw response bytes are not committed.",
            "verification_count": 2, "verification_level": "SINGLE_OPERATOR_RERUN",
        }
        if row["status"] == "PASSED_UNDER_PROTOCOL":
            card["baseline_control_summary"] = f"Manual gate review passed only at verbatim locator: {row['locator']}"
        if row["status"] == "BLOCKED_SOURCE": card["block_reason"] = row["review_basis"]
        if row["status"] == "SOURCE_DRIFT": card["drift_reason"] = row["review_basis"]
        violations = validate_evidence_card(card)
        if violations: raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path = CARDS / f"{eid}.json"; path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (CARDS / f"{eid}.svg").write_text(render_svg(path), encoding="utf-8")
        new_entries.append(registry_entry(card, path))
    replaced = {x["protocol_id"] for x in new_entries}
    registry["cards"] = [x for x in registry["cards"] if x["protocol_id"] not in replaced] + new_entries
    registry["cards"].sort(key=lambda x: x["evidence_id"]); registry["card_count"] = len(registry["cards"]); registry["statistics"] = statistics(registry["cards"])
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed_cards": len(rows), "result_counts": counts, "report_sha256": report_sha, "registry_card_count": registry["card_count"]}, indent=2))


if __name__ == "__main__": main()
