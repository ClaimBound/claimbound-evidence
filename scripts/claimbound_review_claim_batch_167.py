#!/usr/bin/env python3
"""Publish the manually reviewed issue #167 source-boundary cards."""
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
REPORT = ROOT / "artifacts/claim_batch_167_manual_review.json"
EXECUTION = ROOT / "artifacts/claim_batch_167_execution_manifest.json"
PROTOCOL = "CB7K-ISSUE-167-MANUAL-SECTION-REVIEW-2026-07-22-v1"

SOURCE_NAMES = {
    "DOM004-T01": "YouTube GenAI disclosure help",
    "DOM004-T02": "Google DeepMind SynthID",
    "DOM004-T03": "OpenAI DALL-E 3 announcement",
    "DOM004-T04": "YouTube misinformation policies",
    "DOM004-T05": "OpenAI consumer privacy",
    "DOM004-T06": "Meta Community Standards Enforcement Report",
    "DOM004-T07": "C2PA Technical Specification 2.2",
    "DOM005-T01": "Meta explaining ranking",
    "DOM005-T02": "Meta recommendation guidelines",
    "DOM005-T03": "Meta political-content controls announcement",
    "DOM005-T04": "Meta Instagram Teen Accounts announcement",
    "DOM005-T05": "Meta Instagram Feed Recommendations",
    "DOM005-T06": "Meta recommendations explainer",
    "DOM005-T07": "Meta research tools and datasets",
    "DOM006-T01": "Waymo Safety Impact",
    "DOM006-T02": "NHTSA Standing General Order crash reporting",
    "DOM006-T03": "Waymo Safety",
    "DOM006-T04": "Waymo remote assistance article",
    "DOM006-T05": "NHTSA automatic emergency braking rule announcement",
    "DOM006-T06": "Waymo Research",
    "DOM006-T07": "NHTSA automated vehicle safety",
}

# Exact locators reviewed in the frozen local source text. Missing gates remain
# insufficient; no lexical token-counting is used to manufacture a pass.
LOCATORS: dict[str, dict[str, str]] = {
    "DOM004-T01": {
        "source-integrity": "Disclosing use of GenAI content",
        "coverage": "Realistic AI content and meaningful changes require disclosure, while non-realistic or minor edits don’t.",
        "method-version": "the ‘AI use’ setting is available to creators",
        "negative-evidence": "If our systems make an error",
        "conflicts-disclosure": "YouTube Help",
        "overclaim-drift": "Keep in mind, this isn’t a complete list.",
    },
    "DOM004-T02": {
        "source-integrity": "SynthID — Google DeepMind",
        "coverage": "images, audio, text or video",
        "method-version": "SynthID adjusts these probability scores to generate a watermark",
        "negative-evidence": "currently collaborating with journalists and media professionals to test the portal",
        "conflicts-disclosure": "Google DeepMind",
        "overclaim-drift": "currently collaborating with journalists and media professionals to test the portal",
    },
    "DOM004-T04": {
        "source-integrity": "Misinformation policies",
        "coverage": "serious risk of egregious harm",
        "negative-evidence": "We may allow content that violates the misinformation policies",
        "conflicts-disclosure": "YouTube Help",
        "overclaim-drift": "Remember these are just some examples",
    },
    "DOM005-T04": {
        "source-integrity": "Introducing Instagram Teen Accounts: Built-In Protections for Teens, Peace of Mind for Parents",
        "coverage": "all teens under 16",
        "time-boundary": "Originally published on September 17, 2024 at 5:00AM PT",
        "method-version": "automatically place teens into Teen Accounts",
        "negative-evidence": "This measure didn’t work as well as we’d hoped",
        "conflicts-disclosure": "Meta",
        "overclaim-drift": "we need to make sure they work correctly",
    },
    "DOM006-T01": {
        "source-integrity": "Waymo Safety Impact",
        "coverage": "Only data from cities with sufficient Waymo miles for statistical comparisons are shown",
        "time-boundary": "Through March 2026",
        "method-version": "consistent updates aligned with  NHTSA’s Standing General Order",
        "comparator": "average human driver over the same distance in our operating cities",
        "negative-evidence": "error bars represent 95% confidence intervals",
        "conflicts-disclosure": "Waymo Safety Impact",
        "overclaim-drift": "Only data from cities with sufficient Waymo miles for statistical comparisons are shown",
    },
}

GATE_TARGETS = {
    "source-integrity": "The frozen bytes identify an exact official source and a topic-specific boundary for {topic}.",
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


def final_status(headers: str) -> int:
    statuses = [line.split()[1] for line in headers.splitlines() if line.startswith("HTTP/")]
    return int(statuses[-1]) if statuses else 0


def statistics(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "by_domain": dict(sorted(Counter(x["domain"] for x in entries).items())),
        "by_record_type": dict(sorted(Counter(x["record_type"] for x in entries).items())),
        "by_result_status": dict(sorted(Counter(x["result_status"] for x in entries).items())),
        "by_source": dict(sorted(Counter(x["official_source_name"] for x in entries).items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--headers-root", type=Path, required=True)
    parser.add_argument("--text-root", type=Path, required=True)
    parser.add_argument("--operator", required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sources = {x["key"]: x for x in manifest["sources"]}
    if len(sources) != 21:
        raise SystemExit("expected 21 independently frozen topic sources")
    manifest_sha = hashlib.sha256(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    ds = domains(); catalog = make_claims(ds); validate(ds, catalog)
    claims = [c for c in catalog if c["domain_code"] in {"DOM004", "DOM005", "DOM006"}]
    source_rows: dict[str, dict[str, Any]] = {}
    for key, source in sources.items():
        raw = args.raw_root / f"{key}.bin"
        headers = (args.headers_root / f"{key}.txt").read_text(encoding="utf-8", errors="replace")
        text = (args.text_root / f"{key}.txt").read_text(encoding="utf-8")
        source_rows[key] = {
            **source,
            "http_status": final_status(headers),
            "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
            "text": text,
            "canonical_url": "https://spec.c2pa.org/specifications/specifications/2.2/specs/C2PA_Specification.html" if key == "DOM004-T07" else source["source_url"],
        }

    execution_entries = []
    rows = []
    for claim in claims:
        key = source_key(claim); source = source_rows[key]; gate = claim["gate"]
        execution_entries.append({
            "claim_id": claim["claim_id"], "source_url": source["source_url"],
            "evaluation_method": GATE_METHODS[gate],
            "frozen_parameters": {"topic": claim["topic"], "gate": gate},
            "support_rule": GATE_TARGETS[gate].format(topic=claim["topic"]),
            "negative_rule": claim["adjudication_rule"],
        })
        target = GATE_TARGETS[gate].format(topic=claim["topic"])
        if source["http_status"] != 200:
            decision = {"status": "BLOCKED_SOURCE", "locator": f"HTTP {source['http_status']}", "review_basis": "The exact preregistered URL did not return an accessible source; no substitute was selected."}
        elif source["canonical_url"] != source["source_url"]:
            decision = {"status": "SOURCE_DRIFT", "locator": f"selected={source['source_url']} canonical={source['canonical_url']}", "review_basis": "The preregistered URL redirected to a different canonical source boundary before adjudication."}
        elif key not in LOCATORS:
            decision = {"status": "INSUFFICIENT_COVERAGE", "locator": (source["text"].splitlines() or ["empty extracted text"])[0], "review_basis": "The frozen response was a shell, broad index, or topic-mismatched page and did not expose gate-specific evidence."}
        elif gate in LOCATORS[key]:
            locator = LOCATORS[key][gate]
            if locator.casefold() not in source["text"].casefold():
                raise SystemExit(f"{claim['claim_id']}: locator absent: {locator!r}")
            decision = {"status": "PASSED_UNDER_PROTOCOL", "locator": locator, "review_basis": f"Manual review found the gate-specific disclosure at verbatim locator: {locator}."}
        else:
            decision = {"status": "INSUFFICIENT_COVERAGE", "locator": LOCATORS[key]["source-integrity"], "review_basis": "The topic-specific source was reviewed, but it does not disclose the complete gate-specific evidence required here."}
        rows.append({**claim, **decision, "target_statement": target, "source_name": SOURCE_NAMES[key], "source_url": source["source_url"], "canonical_url": source["canonical_url"], "http_status": source["http_status"], "source_sha256": source["sha256"]})

    EXECUTION.write_text(json.dumps({
        "issue_number": 167,
        "source_manifest_sha256": manifest_sha,
        "claim_boundary": "Claim-level execution plan for issue #167 only; it is not evidence and predeclares no outcome.",
        "raw_payload_committed": False,
        "entries": execution_entries,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = dict(Counter(x["status"] for x in rows))
    REPORT.write_text(json.dumps({"issue_number": 167, "protocol_version": PROTOCOL, "source_manifest_sha256": manifest_sha, "claim_boundary": "Manual gate review of 21 preregistered topic URLs for issue #167; no source replacement after observation.", "operator": args.operator, "raw_payload_committed": False, "review_method": "explicit verbatim locator matrix; no token-count outcome assignment", "result_counts": counts, "cards": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_sha = hashlib.sha256(REPORT.read_bytes()).hexdigest()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sequence = max(x["registry_sequence"] for x in registry["cards"])
    new_entries = []
    for row in rows:
        sequence += 1
        eid = f"CLAIMBOUND-{row['claim_id']}-2026-07-22"
        card = {
            "access_date": "2026-07-22", "ai_assistance": "AI-assisted extraction and consistency checks; outcomes are fixed by an explicit manual gate matrix.",
            "card_svg_rendered": f"docs/evidence_cards/{eid}.svg", "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
            "claim_boundary": row["target_statement"] + " This card is limited to one preregistered source boundary.", "claim_type": "source_boundary", "created_at": "2026-07-22", "domain": row["domain_slug"], "evidence_id": eid,
            "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json", "execution_mode": "AUTOMATED_AI_ASSISTED", "git_commit": "local-before-merge",
            "known_limitations": ["One exact source boundary only; no domain-wide certification.", "A pass applies only to the named gate and locator.", "Insufficient coverage is not a negative result."],
            "last_verified_date": "2026-07-22", "manual_review": row["review_basis"] + f" Locator: {row['locator']}", "official_source_name": row["source_name"], "official_source_url": row["source_url"], "operator": args.operator,
            "protocol_id": row["claim_id"], "protocol_version": PROTOCOL, "raw_payload_committed": False,
            "raw_payload_manifest": f"HTTP {row['http_status']}; canonical {row['canonical_url']}; SHA-256 {row['source_sha256']}; source manifest {manifest_sha}; raw bytes retained locally only",
            "record_type": "source_audit", "registry_sequence": sequence, "reproduction_level": "not independently reproduced", "result_status": row["status"],
            "runner_command": "python scripts/claimbound_review_claim_batch_167.py --manifest <local> --raw-root <local> --headers-root <local> --text-root <local> --operator <handle>",
            "sanitized_report_path": str(REPORT.relative_to(ROOT)), "sanitized_report_sha256": report_sha, "source_rights_note": "Official public source; raw response bytes are not committed.",
            "verification_count": 1, "verification_level": "SINGLE_OPERATOR",
        }
        if row["status"] == "PASSED_UNDER_PROTOCOL": card["baseline_control_summary"] = f"Manual gate review passed only at verbatim locator: {row['locator']}"
        if row["status"] == "BLOCKED_SOURCE": card["block_reason"] = row["review_basis"]
        if row["status"] == "SOURCE_DRIFT": card["drift_reason"] = row["review_basis"]
        violations = validate_evidence_card(card)
        if violations: raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path = CARDS / f"{eid}.json"; path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (CARDS / f"{eid}.svg").write_text(render_svg(path), encoding="utf-8")
        new_entries.append({k: card[k] for k in ("evidence_id", "registry_sequence", "result_status", "protocol_id", "domain", "record_type", "operator", "created_at", "last_verified_date", "verification_level", "verification_count", "reproduction_level", "official_source_name", "sanitized_report_path")} | {"path": str(path.relative_to(ROOT))})
    registry["cards"].extend(new_entries); registry["cards"].sort(key=lambda x: x["evidence_id"]); registry["card_count"] = len(registry["cards"]); registry["statistics"] = statistics(registry["cards"])
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed_cards": len(rows), "result_counts": counts, "registry_card_count": registry["card_count"], "report_sha256": report_sha}, indent=2))


if __name__ == "__main__":
    main()
