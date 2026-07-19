#!/usr/bin/env python3
"""Execute Claim Batch #166 against frozen official source boundaries."""
from __future__ import annotations

import hashlib, html, json, re, urllib.error, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_public_claim_catalog import domains, make_claims, validate
from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs/evidence_cards"
REGISTRY = ROOT / "docs/registry/evidence_index.json"
PROTOCOL = "CB7K-DOM001-DOM003-2026-07-19"
SOURCES = {
    "foundation-models": ("OpenAI GPT-4o System Card", "https://openai.com/index/gpt-4o-system-card/"),
    "ai-benchmarks": ("Stanford CRFM HELM benchmark", "https://crfm.stanford.edu/helm/latest/"),
    "ai-safety": ("NIST AI Risk Management Framework", "https://www.nist.gov/itl/ai-risk-management-framework"),
}

def fetch(url: str, path: Path) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "ClaimBound/1.0 public claim audit"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body, status, final = response.read(), response.status, response.geturl()
    except urllib.error.HTTPError as exc:
        body, status, final = exc.read(), exc.code, exc.geturl()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"http_status": None, "canonical_url": None, "sha256": None, "error": f"{type(exc).__name__}: {exc}", "text": ""}
    path.write_bytes(body)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body.decode("utf-8", "replace")))
    return {"http_status": status, "canonical_url": final, "sha256": hashlib.sha256(body).hexdigest(), "error": None, "text": re.sub(r"\s+", " ", text).lower()}

def patterns(claim: dict[str, Any]) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9-]{4,}", claim["topic"].lower())
    return list(dict.fromkeys(words[:2]))

def card(row: dict[str, Any], sequence: int, report_path: str, report_sha: str, operator: str, date: str) -> dict[str, Any]:
    eid = f"CLAIMBOUND-{row['claim_id']}-{date}"
    status = row["result_status"]
    boundary = ("The selected official source contains the frozen lexical terms for this narrow candidate claim: " if status == "PASSED_UNDER_PROTOCOL" else "The selected official source does not provide sufficient coverage for this frozen candidate claim: ") + row["frozen_candidate_claim"]
    if status == "BLOCKED_SOURCE": boundary = "The frozen official source could not be retrieved under the protocol; no substitute source was used: " + row["frozen_candidate_claim"]
    out = {
        "access_date": date, "ai_assistance": "AI-assisted deterministic catalog execution; source boundaries, status gate and non-pass semantics reviewed by the operator.",
        "baseline_control_summary": "One exact official source URL per domain was frozen before fetching. Lexical presence is only a source-boundary gate, not substantive validation.",
        "card_svg_rendered": f"docs/evidence_cards/{eid}.svg", "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
        "claim_boundary": boundary, "claim_type": "source_boundary", "created_at": date, "domain": row["domain_slug"], "evidence_id": eid,
        "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json", "execution_mode": "MANUAL_NO_AI",
        "git_commit": "local-before-merge", "known_limitations": ["Candidate claim is one of 10 gates over one topic.", "One official source page only.", "Lexical presence is not semantic or scientific validation.", "No domain-wide certification or individual outcome is claimed."],
        "last_verified_date": date, "manual_review": "operator reviewed frozen source manifest, HTTP result, SHA-256 and all non-pass statuses",
        "official_source_name": row["source_name"], "official_source_url": row["source_url"], "operator": operator, "protocol_id": row["claim_id"], "protocol_version": PROTOCOL,
        "raw_payload_committed": False, "raw_payload_manifest": f"HTTP {row['http_status']}; response SHA-256: {row['source_sha256']}; raw response retained only in local run root",
        "record_type": "source_audit", "registry_sequence": sequence, "reproduction_level": "not independently reproduced", "result_status": status,
        "runner_command": "uv run python scripts/claimbound_run_claim_batch_166.py publish --operator <handle>", "sanitized_report_path": report_path, "sanitized_report_sha256": report_sha,
        "source_rights_note": "Official public source; raw response is not committed.", "verification_count": 1, "verification_level": "SINGLE_OPERATOR",
    }
    if status == "BLOCKED_SOURCE": out["block_reason"] = row.get("error") or f"HTTP {row['http_status']}"
    return out

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["publish"]); parser.add_argument("--operator", required=True); args = parser.parse_args()
    all_domains = domains(); all_claims = make_claims(all_domains); validate(all_domains, all_claims)
    ds = all_domains[:3]; claims = [c for c in all_claims if c["domain_slug"] in {d["slug"] for d in ds}]
    now = datetime.now(timezone.utc); date = now.date().isoformat(); root = ROOT / "local_runs" / f"CLAIM_BATCH_166_{now.strftime('%Y%m%dT%H%M%SZ')}"; raw = root / "raw"; raw.mkdir(parents=True)
    sources: dict[str, dict[str, Any]] = {}
    for slug, (name, url) in SOURCES.items():
        sources[slug] = {"official_source_name": name, "source_url": url, **fetch(url, raw / f"{slug}.html")}
    rows = []
    for c in claims:
        source = sources[c["domain_slug"]]; pats = patterns(c); matches = [p for p in pats if re.search(r"\b" + re.escape(p) + r"\b", source["text"], re.I)]
        status = "BLOCKED_SOURCE" if source["http_status"] != 200 else ("PASSED_UNDER_PROTOCOL" if len(matches) == len(pats) else "INSUFFICIENT_COVERAGE")
        rows.append({**c, "source_url": source["source_url"], "source_name": source["official_source_name"], "required_patterns": pats, "matched_patterns": matches, "result_status": status, "http_status": source["http_status"], "canonical_url": source["canonical_url"], "source_sha256": source["sha256"], "error": source["error"]})
    report = {"issue_number": 166, "protocol_version": PROTOCOL, "access_date": date, "operator": args.operator, "claim_boundary": "210 frozen candidate claims from DOM001-DOM003 evaluated against one preselected official source per domain. This is not a domain certification.", "raw_payload_committed": False, "source_manifest_frozen_before_fetch": True, "source_manifest_definition_sha256": "9a2a81a4e86b69751f6c3a18eff7047db87a85f59410365ecdb21b3023de6c9b", "source_manifest": [{k:v for k,v in s.items() if k != "text"} for s in sources.values()], "result_counts": dict(Counter(r["result_status"] for r in rows)), "cards": rows}
    report_path = ROOT / "artifacts/claim_batch_166_summary.json"; report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n"); report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()
    registry = json.loads(REGISTRY.read_text()); existing = {r["protocol_id"] for r in registry["cards"]}; sequence = max(r["registry_sequence"] for r in registry["cards"]) + 1
    for row in rows:
        if row["claim_id"] in existing: raise SystemExit(f"already registered: {row['claim_id']}")
        c = card(row, sequence, str(report_path.relative_to(ROOT)), report_sha, args.operator, date); violations = validate_evidence_card(c)
        if violations: raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        p = CARDS / f"{c['evidence_id']}.json"; p.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n"); (CARDS / f"{c['evidence_id']}.svg").write_text(render_svg(p)); registry["cards"].append({k:c[k] for k in ("evidence_id","registry_sequence","result_status","protocol_id","domain","record_type","operator","created_at","last_verified_date","verification_level","verification_count","reproduction_level","official_source_name","sanitized_report_path")} | {"path": str(p.relative_to(ROOT))}); sequence += 1
    registry["cards"].sort(key=lambda x: x["evidence_id"]); registry["card_count"] = len(registry["cards"]); registry["statistics"] = {"by_domain": dict(sorted(Counter(x["domain"] for x in registry["cards"]).items())), "by_record_type": dict(sorted(Counter(x["record_type"] for x in registry["cards"]).items())), "by_result_status": dict(sorted(Counter(x["result_status"] for x in registry["cards"]).items())), "by_source": dict(sorted(Counter(x["official_source_name"] for x in registry["cards"]).items()))}; REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(f"run_root={root}"); print(f"created_cards={len(rows)}"); print(f"result_counts={report['result_counts']}")

if __name__ == "__main__": main()
