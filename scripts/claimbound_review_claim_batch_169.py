#!/usr/bin/env python3
"""Publish conservatively reviewed issue #169 source-boundary cards."""
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
REPORT = ROOT / "artifacts/claim_batch_169_manual_review.json"
EXECUTION = ROOT / "artifacts/claim_batch_169_execution_manifest.json"
PROTOCOL = "CB7K-ISSUE-169-CONSERVATIVE-LOCATOR-REVIEW-2026-07-22-v1"

SOURCE_NAMES = {
    "DOM010-T01": "NIST NVD CVE-2026-34181", "DOM010-T02": "NIST SP 1800-31 enterprise patching",
    "DOM010-T03": "CISA recommended practices for SBOM consumption", "DOM010-T04": "NIST SP 800-115 security testing",
    "DOM010-T05": "NIST SP 1800-16 TLS server certificate management", "DOM010-T06": "NIST SP 800-61 Rev. 3 incident response",
    "DOM010-T07": "NIST Cryptographic Module Validation Program",
    "DOM011-T01": "CISA SBOM Resources Library", "DOM011-T02": "SLSA Provenance specification",
    "DOM011-T03": "Sigstore verifying releases", "DOM011-T04": "CISA recommended practices for SBOM consumption",
    "DOM011-T05": "CISA securing the software supply chain for developers", "DOM011-T06": "SLSA source-track basics",
    "DOM011-T07": "CISA managing OSS and SBOMs",
    "DOM012-T01": "Reproducible Builds definition", "DOM012-T02": "Reproducible Builds build environment",
    "DOM012-T03": "Reproducible Builds stable inputs", "DOM012-T04": "Reproducible Builds timestamps",
    "DOM012-T05": "Reproducible Builds system images", "DOM012-T06": "Reproducible Builds embedded signatures",
    "DOM012-T07": "Reproducible Builds version information",
}

# Every pass below is tied to a verbatim locator in the frozen local extraction.
# Sources absent from this matrix, and gates absent within a source, are insufficient.
LOCATORS: dict[str, dict[str, str]] = {
    "DOM010-T01": {
        "source-integrity": "NVD - CVE-2026-34181",
        "numerator-denominator": "with a 1 in 256 probability",
        "coverage": "The FIPS modules are not affected by this issue",
        "method-version": "CVSS Version 4.0",
        "negative-evidence": "allowing a certificate and private key forgery",
        "overclaim-drift": "NIST does not necessarily endorse the views expressed",
    },
    "DOM010-T02": {
        "source-integrity": "Improving Enterprise Patching for General IT Systems: Utilizing Existing Tools and Performing Processes in Better Ways",
        "coverage": "both routine and emergency patching situations",
        "method-version": "test patches before deployment",
        "negative-evidence": "many organizations cannot or do not adequately patch",
        "overclaim-drift": "the act of patching can reduce system and service availability",
    },
    "DOM010-T03": {
        "source-integrity": "Securing the Software Supply Chain: Recommended Practices for SBOM Consumption",
        "coverage": "discovered “zero-day” vulnerabilities.",
        "method-version": "Zero-day” vulnerabilities can be identified in vulnerability databases",
        "negative-evidence": "This does not guarantee that the",
        "overclaim-drift": "constitute compliance or legal advice.",
    },
    "DOM010-T04": {
        "source-integrity": "The purpose of this document is to assist organizations in planning and conducting technical information security tests and examinations",
        "coverage": "finding vulnerabilities in a system or network and verifying compliance",
        "method-version": "designing, implementing, and maintaining technical information security test and examination processes and procedures",
        "negative-evidence": "the benefits and limitations of each",
        "overclaim-drift": "not intended to present a comprehensive information security testing and examination program",
    },
    "DOM010-T06": {
        "source-integrity": "Incident Response Recommendations and Considerations for Cybersecurity Risk Management",
        "coverage": "incident response",
    },
    "DOM010-T07": {
        "source-integrity": "FIPS Validation and Updates, Patches, and CVEs",
        "coverage": "The tested/validated module version, operational environment upon which it was tested, and the originating vendor",
        "method-version": "Changing the code of the module results in that portion being untested",
        "negative-evidence": "the new version that includes the patch/update would not be validated",
        "overclaim-drift": "not a decision the CMVP has either the information necessary or the authority to make",
    },
    "DOM011-T02": {
        "source-integrity": "SLSA • Provenance",
        "coverage": "through all the moving parts in a complex supply chain",
        "method-version": "describing where, when, and how something was produced",
        "overclaim-drift": "may have their own, more specific, implementations of provenance",
    },
    "DOM011-T03": {
        "source-integrity": "Verifying Binaries",
        "coverage": "download the signature and signing certificate from the same release",
        "method-version": "Verify the certificate chain",
        "reproducibility": "With the above three files, we can now perform a rudimentary verification.",
        "overclaim-drift": "For now this is quite a multi step process.",
    },
    "DOM011-T04": {
        "source-integrity": "Securing the Software Supply Chain: Recommended Practices for SBOM Consumption",
        "coverage": "known vulnerabilities associated with SBOM’s",
        "time-boundary": "discovered “zero-day” vulnerabilities.",
        "method-version": "risk can be re-assessed due to changes in environment",
        "negative-evidence": "there may not be any currently known",
        "overclaim-drift": "This does not guarantee that the",
    },
    "DOM011-T05": {
        "source-integrity": "Securing the Software Supply Chain: Recommended Practices for Developers",
        "coverage": "two types of build environments, the individual developer environment",
        "method-version": "Harden the Build Environment",
        "negative-evidence": "Unmitigated vulnerabilities in the software supply chain pose a significant risk",
        "overclaim-drift": "does not, and is not intended to, constitute compliance or legal advice",
    },
    "DOM011-T07": {
        "source-integrity": "Securing the Software Supply Chain: Recommended Practices for Managing OSS and SBOMs",
        "coverage": "components, versions, and dependencies (internal and external)",
        "method-version": "four major categories, source, binary",
        "negative-evidence": "source extractors may not yield the precise dependencies for all delivered product architectures",
        "overclaim-drift": "a more complex solution and not readily available for all environments.",
    },
    "DOM012-T01": {
        "source-integrity": "Definitions — reproducible-builds.org",
        "coverage": "same source code, build environment and build instructions",
        "method-version": "any party can recreate bit-by-bit identical copies of all specified artifacts",
        "reproducibility": "any party can recreate bit-by-bit identical copies",
        "overclaim-drift": "The relevant attributes of the build environment, the build instructions and the source code",
    },
    "DOM012-T03": {
        "source-integrity": "Stable order for inputs — reproducible-builds.org",
        "coverage": "Most filesystems do not guarantee that listing files in a directory always results in the same order.",
        "method-version": "Stable order for inputs",
        "negative-evidence": "can result in unreproducible builds",
    },
    "DOM012-T04": {
        "source-integrity": "Timestamps — reproducible-builds.org",
        "coverage": "Many build tools record the current date and time.",
        "method-version": "SOURCE_DATE_EPOCH",
        "negative-evidence": "things will go wrong",
        "overclaim-drift": "So beware.",
    },
    "DOM012-T05": {
        "source-integrity": "System images — reproducible-builds.org",
        "coverage": "VM and cloud images, live systems, OS installer ISO images",
        "method-version": "make_ext4fs -T <unix_timestamp>",
        "negative-evidence": "the allocation of the inodes is undefined",
        "overclaim-drift": "This documentation’s intent is to share what we currently know",
    },
    "DOM012-T06": {
        "source-integrity": "Embedded signatures — reproducible-builds.org",
        "coverage": "signature part of the build process input",
        "method-version": "compare to builds skipping the signatures",
        "negative-evidence": "they will not be able to generate an identical signature",
        "overclaim-drift": "can pose a challenge to allow users to reproduce identical results",
    },
    "DOM012-T07": {
        "source-integrity": "Version information — reproducible-builds.org",
        "coverage": "what source code has been built",
        "method-version": "commit IDs are thus a good candidate",
        "negative-evidence": "can be a source of non-reproducibility",
        "overclaim-drift": "an old source code can always be compiled long after it has been released",
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
    if len(sources) != 21 or any(len({x["source_url"] for x in manifest["sources"] if x["key"].startswith(d)}) < 7 for d in ("DOM010", "DOM011", "DOM012")):
        raise SystemExit("expected seven independently frozen topic URLs per domain")
    manifest_sha = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    ds = domains(); catalog = make_claims(ds); validate(ds, catalog)
    claims = [c for c in catalog if c["domain_code"] in {"DOM010", "DOM011", "DOM012"}]
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
    EXECUTION.write_text(json.dumps({"issue_number": 169, "source_manifest_sha256": manifest_sha, "claim_boundary": "Claim-level execution plan for issue #169 only; it is not evidence and predeclares no outcome.", "raw_payload_committed": False, "entries": execution}, indent=2, ensure_ascii=False) + "\n")
    counts = dict(Counter(x["status"] for x in rows))
    REPORT.write_text(json.dumps({"issue_number": 169, "protocol_version": PROTOCOL, "source_manifest_sha256": manifest_sha, "claim_boundary": "Conservative manual review of 21 preregistered NIST, CISA, SLSA, Sigstore and Reproducible Builds topic URLs for issue #169; no source replacement after observation.", "operator": args.operator, "raw_payload_committed": False, "review_method": "explicit gate-to-verbatim-locator matrix; unreviewed or incomplete gates remain insufficient", "result_counts": counts, "cards": rows}, indent=2, ensure_ascii=False) + "\n")
    report_sha = hashlib.sha256(REPORT.read_bytes()).hexdigest(); registry = json.loads(REGISTRY.read_text()); sequence = max(x["registry_sequence"] for x in registry["cards"]); new_entries = []
    for row in rows:
        sequence += 1; eid = f"CLAIMBOUND-{row['claim_id']}-2026-07-22"
        limitations = ["One exact source boundary only; no domain-wide certification.", "A pass applies only to the named gate and verbatim locator.", "Insufficient coverage is not a negative result."]
        card = {"access_date": "2026-07-22", "ai_assistance": "AI-assisted extraction and consistency checks; outcomes are fixed by an explicit conservative locator matrix.", "card_svg_rendered": f"docs/evidence_cards/{eid}.svg", "card_svg_template": "docs/assets/claimbound_evidence_card.svg", "claim_boundary": row["target_statement"] + " This card is limited to one preregistered source boundary.", "claim_type": "source_boundary", "created_at": "2026-07-22", "domain": row["domain_slug"], "evidence_id": eid, "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json", "execution_mode": "AUTOMATED_AI_ASSISTED", "git_commit": "local-before-merge", "known_limitations": limitations, "last_verified_date": "2026-07-22", "manual_review": row["review_basis"] + f" Locator: {row['locator']}", "official_source_name": row["source_name"], "official_source_url": row["source_url"], "operator": args.operator, "protocol_id": row["claim_id"], "protocol_version": PROTOCOL, "raw_payload_committed": False, "raw_payload_manifest": f"HTTP {row['http_status']}; canonical {row['canonical_url']}; SHA-256 {row['source_sha256']}; source manifest {manifest_sha}; raw bytes retained locally only", "record_type": "source_audit", "registry_sequence": sequence, "reproduction_level": "not independently reproduced", "result_status": row["status"], "runner_command": "python scripts/claimbound_review_claim_batch_169.py --manifest <local> --raw-root <local> --meta-root <local> --text-root <local> --operator <handle>", "sanitized_report_path": str(REPORT.relative_to(ROOT)), "sanitized_report_sha256": report_sha, "source_rights_note": "Public documentation source; raw response bytes are not committed.", "verification_count": 1, "verification_level": "SINGLE_OPERATOR"}
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
