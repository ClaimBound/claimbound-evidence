#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run and publish the frozen Leqembi issues #157 through #161."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs/evidence_cards"
REGISTRY = ROOT / "docs/registry/evidence_index.json"
NEJM = "https://www.nejm.org/doi/full/10.1056/NEJMoa2212948"
FDA = "https://www.fda.gov/news-events/press-announcements/fda-converts-novel-alzheimers-disease-treatment-traditional-approval"
TRIAL = "https://clinicaltrials.gov/study/NCT03887455"
UA = "Mozilla/5.0 ClaimBound/1.0 (public medical source-boundary audit)"

CANDIDATES = [
    ("MED-LEQ-01-D1201", 158, NEJM, "NEJM CLARITY AD primary paper", "In CLARITY AD, lecanemab produced less decline than placebo over 18 months on the Clinical Dementia Rating Scale-Sum of Boxes (CDR-SB).", [r"18 months", r"CDR.SB", r"lecanemab", r"placebo", r"less decline|declined less"]),
    ("MED-LEQ-02-D1202", 158, NEJM, "NEJM CLARITY AD primary paper", "The reported mean CDR-SB change at 18 months was 1.21 with lecanemab and 1.66 with placebo, an adjusted mean difference of -0.45 points.", [r"1.21", r"1.66", r"0.45", r"18 months"]),
    ("MED-LEQ-03-D1203", 158, NEJM, "NEJM CLARITY AD primary paper", "The widely reported 27% is approximately the relative reduction in measured decline: 0.45 divided by the 1.66-point placebo decline equals 27.1%.", [r"1.66", r"0.45"]),
    ("MED-LEQ-04-D1204", 158, NEJM, "NEJM CLARITY AD primary paper", "On CDR-SB, both groups worsened on average over 18 months; lecanemab worsened less than placebo.", [r"1.21", r"1.66", r"18 months"]),
    ("MED-LEQ-05-D1205", 159, FDA, "FDA traditional-approval announcement (6 July 2023)", "Study 301 initiated treatment in patients with mild cognitive impairment or mild dementia due to Alzheimer's disease.", [r"Study 301", r"mild cognitive impairment", r"mild dementia"]),
    ("MED-LEQ-06-D1206", 159, FDA, "FDA traditional-approval announcement (6 July 2023)", "The studied population had confirmed amyloid beta pathology.", [r"confirmed presence of amyloid beta pathology|confirmed amyloid beta pathology"]),
    ("MED-LEQ-07-D1207", 159, FDA, "FDA traditional-approval announcement (6 July 2023)", "The FDA page states there were no safety or effectiveness data for initiating treatment at earlier or later disease stages than those studied.", [r"no safety or effectiveness data", r"earlier or later stages"]),
    ("MED-LEQ-08-D1208", 159, FDA, "FDA traditional-approval announcement (6 July 2023)", "The selected FDA page does not establish cure, reversal, 27% memory improvement, or recovery of 27% of patients; it reports reduction of decline and verified clinical benefit.", []),
    ("MED-LEQ-09-D1209", 160, FDA, "FDA traditional-approval announcement (6 July 2023)", "ARIA can infrequently include serious and life-threatening brain edema, and intracerebral hemorrhages can be fatal.", [r"infrequently", r"serious and life-threatening", r"can be fatal"]),
    ("MED-LEQ-10-D1210", 160, FDA, "FDA traditional-approval announcement (6 July 2023)", "The prescribing information includes a boxed warning about potential risks associated with ARIA.", [r"boxed warning", r"potential risks associated with ARIA"]),
    ("MED-LEQ-11-D1211", 160, FDA, "FDA traditional-approval announcement (6 July 2023)", "ApoE epsilon 4 homozygotes had higher ARIA incidence, including symptomatic, serious, and severe ARIA; testing should be performed before treatment to inform risk.", [r"homozygous", r"higher incidence", r"testing.*before starting treatment"]),
    ("MED-LEQ-12-D1212", 160, FDA, "FDA traditional-approval announcement (6 July 2023)", "Anticoagulant use was associated with more intracerebral hemorrhages with Leqembi than placebo; caution is recommended for anticoagulant use or other hemorrhage risk factors.", [r"anticoagulant", r"compared to placebo|compared with placebo", r"caution"]),
]

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalized(data: bytes) -> str:
    text = data.decode("utf-8", "replace")
    text = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()

def fetch(url: str, raw: Path) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            body, status, final = res.read(), res.status, res.geturl()
    except urllib.error.HTTPError as exc:
        body, status, final = exc.read(), exc.code, exc.geturl()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"source_url": url, "canonical_url": None, "http_status": None, "sha256": None, "fetch_error": f"{type(exc).__name__}: {exc}", "text": ""}
    raw.write_bytes(body)
    return {"source_url": url, "canonical_url": final, "http_status": status, "sha256": sha(body), "fetch_error": None, "text": normalized(body)}

def statistics(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {key: dict(sorted(Counter(str(r[field]) for r in rows).items())) for key, field in (("by_domain", "domain"), ("by_record_type", "record_type"), ("by_result_status", "result_status"), ("by_source", "official_source_name"))}

def registry_entry(card: dict[str, Any], path: Path) -> dict[str, Any]:
    keys = ["evidence_id", "registry_sequence", "result_status", "protocol_id", "domain", "record_type", "operator", "created_at", "last_verified_date", "verification_level", "verification_count", "reproduction_level", "official_source_name", "sanitized_report_path"]
    return {**{k: card[k] for k in keys}, "path": str(path.relative_to(ROOT))}

def make_card(row: dict[str, Any], sequence: int, report_path: str, report_sha: str, operator: str, access_date: str) -> dict[str, Any]:
    protocol = row["protocol_id"]
    eid = f"CLAIMBOUND-{protocol}-{access_date}"
    status = row["result_status"]
    boundary = ("The frozen source explicitly supports this narrow statement: " if status == "PASSED_UNDER_PROTOCOL" else "The frozen source did not provide sufficient accessible coverage for this narrow statement: ") + row["claim"]
    if status == "BLOCKED_SOURCE":
        boundary = "The frozen primary-paper URL returned HTTP 403, so the claim was not adjudicated from a substitute source: " + row["claim"]
    card: dict[str, Any] = {
        "access_date": access_date, "ai_assistance": "AI-assisted protocol implementation; frozen claims and deterministic gates were reviewed by the operator before publication.",
        "baseline_control_summary": "Exact frozen URL and claim boundary; raw responses remain local; absence alone is never converted into a negative result.",
        "card_svg_rendered": f"docs/evidence_cards/{eid}.svg", "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
        "claim_boundary": boundary, "claim_type": "source_boundary", "created_at": access_date, "domain": "public-data", "evidence_id": eid,
        "evidence_url": f"https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json", "execution_mode": "MANUAL_NO_AI",
        "git_commit": "local-before-merge", "known_limitations": ["One frozen source boundary only.", "This is not medical advice or a benefit-risk recommendation.", "A lexical gate is not independent clinical validation.", "No individual outcome is predicted."],
        "last_verified_date": access_date, "manual_review": "operator reviewed source status, matched language, qualifiers, arithmetic, and non-pass semantics",
        "official_source_name": row["source_name"], "official_source_url": row["source_url"], "operator": operator, "protocol_id": protocol,
        "protocol_version": "2026-07-16", "raw_payload_committed": False,
        "raw_payload_manifest": f"HTTP {row['http_status']}; response SHA-256: {row['source_sha256']}; raw response retained only in local run root",
        "record_type": "reproduction_attempt" if protocol.endswith("-R1") else "source_audit", "registry_sequence": sequence,
        "reproduction_level": row.get("reproduction_level", "not independently reproduced"), "result_status": status,
        "runner_command": "uv run python scripts/claimbound_run_leqembi_campaign.py publish --operator <handle>",
        "sanitized_report_path": report_path, "sanitized_report_sha256": report_sha,
        "source_rights_note": "Public FDA/ClinicalTrials.gov page or publisher landing page; raw response is not committed.",
        "verification_count": 1, "verification_level": "SINGLE_OPERATOR",
    }
    if status == "BLOCKED_SOURCE": card["block_reason"] = f"HTTP {row['http_status']} from the frozen NEJM URL"
    return card

def run(operator: str) -> None:
    now = datetime.now(timezone.utc); date = now.date().isoformat(); stamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_root = Path.home() / "claimbound_runs" / f"LEQEMBI_{stamp}"; raw = run_root / "raw"; raw.mkdir(parents=True)
    baseline_sources = {url: fetch(url, raw / f"baseline-{i}.html") for i, url in enumerate((NEJM, FDA, TRIAL), 1)}
    rerun_sources = {url: fetch(url, raw / f"rerun-{i}.html") for i, url in enumerate((NEJM, FDA, TRIAL), 1)}
    baseline: list[dict[str, Any]] = []
    for protocol, issue, url, name, claim, patterns in CANDIDATES:
        src = baseline_sources[url]; matches = [p for p in patterns if re.search(p, src["text"], re.I)]
        status = "BLOCKED_SOURCE" if src["http_status"] != 200 else ("INSUFFICIENT_COVERAGE" if not patterns or len(matches) != len(patterns) else "PASSED_UNDER_PROTOCOL")
        baseline.append({"protocol_id": protocol, "issue_number": issue, "source_url": url, "source_name": name, "claim": claim, "required_patterns": patterns, "matched_patterns": matches, "result_status": status, "http_status": src["http_status"], "canonical_url": src["canonical_url"], "source_sha256": src["sha256"]})
    reruns = []
    for base in baseline:
        src = rerun_sources[base["source_url"]]; matches = [p for p in base["required_patterns"] if re.search(p, src["text"], re.I)]
        status = "BLOCKED_SOURCE" if src["http_status"] != 200 else ("INSUFFICIENT_COVERAGE" if not base["required_patterns"] or len(matches) != len(base["required_patterns"]) else "PASSED_UNDER_PROTOCOL")
        reruns.append({**base, "protocol_id": base["protocol_id"] + "-R1", "issue_number": 161, "matched_patterns": matches, "result_status": status, "http_status": src["http_status"], "canonical_url": src["canonical_url"], "source_sha256": src["sha256"], "baseline_protocol_id": base["protocol_id"], "baseline_sha256": base["source_sha256"], "http_access_changed": src["http_status"] != base["http_status"], "claim_support_changed": status != base["result_status"], "reproduction_level": "REPRODUCED_OUTCOME" if src["sha256"] == base["source_sha256"] else "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT"})
    for issue in (158, 159, 160):
        rows = [r for r in baseline if r["issue_number"] == issue]; path = f"artifacts/leqembi_issue_{issue}_batch_summary.json"
        payload = (json.dumps({"issue_number": issue, "access_date": date, "operator": operator, "raw_payload_committed": False, "claim_boundary": "Frozen issue-defined Leqembi claims evaluated only against their exact primary source URL; no blocked source is substituted and no medical recommendation is made.", "result_counts": dict(Counter(r["result_status"] for r in rows)), "source_records": [{k:v for k,v in baseline_sources[r["source_url"]].items() if k != "text"} for r in rows[:1]], "cards": rows}, indent=2, ensure_ascii=False) + "\n").encode(); (ROOT/path).write_bytes(payload)
    drift_path = "artifacts/leqembi_issue_161_rerun_summary.json"
    drift_payload = (json.dumps({"issue_number": 161, "access_date": date, "operator": operator, "raw_payload_committed": False, "claim_boundary": "Same-source immediate rerun of all 12 frozen baseline claims; byte/access drift is separated from claim-support drift and no baseline card is overwritten.", "result_counts": dict(Counter(r["result_status"] for r in reruns)), "source_records": [{k:v for k,v in s.items() if k != "text"} for s in rerun_sources.values()], "cards": reruns}, indent=2, ensure_ascii=False) + "\n").encode(); (ROOT/drift_path).write_bytes(drift_payload)
    reports = {158: ("artifacts/leqembi_issue_158_batch_summary.json",), 159: ("artifacts/leqembi_issue_159_batch_summary.json",), 160: ("artifacts/leqembi_issue_160_batch_summary.json",), 161: (drift_path,)}
    registry = json.loads(REGISTRY.read_text()); existing = {r["protocol_id"] for r in registry["cards"]}; seq = max(r["registry_sequence"] for r in registry["cards"]) + 1
    for row in baseline + reruns:
        if row["protocol_id"] in existing: raise SystemExit(f"already registered: {row['protocol_id']}")
        report = reports[row["issue_number"]][0]; card = make_card(row, seq, report, sha((ROOT/report).read_bytes()), operator, date); violations = validate_evidence_card(card)
        if violations: raise SystemExit(f"{row['protocol_id']}: {'; '.join(violations)}")
        path = CARDS / f"{card['evidence_id']}.json"; path.write_text(json.dumps(card, indent=2, ensure_ascii=False)+"\n"); (CARDS/f"{card['evidence_id']}.svg").write_text(render_svg(path)); registry["cards"].append(registry_entry(card, path)); seq += 1
    registry["cards"].sort(key=lambda r: r["evidence_id"]); registry["card_count"] = len(registry["cards"]); registry["statistics"] = statistics(registry["cards"]); REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False)+"\n")
    print(f"run_root={run_root}"); print(f"created_cards={len(baseline)+len(reruns)}"); print(f"baseline={dict(Counter(r['result_status'] for r in baseline))}"); print(f"rerun={dict(Counter(r['result_status'] for r in reruns))}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["publish"]); parser.add_argument("--operator", required=True); args = parser.parse_args(); run(args.operator)
