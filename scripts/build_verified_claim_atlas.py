#!/usr/bin/env python3
"""Build the transparent CB7K results and protocol-audit atlas."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_cb7k_campaign import (
    audit_campaign,
    load_execution_entries,
    load_review_records,
    reason_code,
)
from build_public_claim_catalog import (
    GATE_METHODS,
    GATE_SOURCE_ROLES,
    ROOT,
    domains,
    make_claims,
)

CARD_RE = re.compile(
    r"CLAIMBOUND-(CB7K-DOM\d{3}-T\d{2}-G\d{2})-\d{4}-\d{2}-\d{2}\.json$"
)
RAW_HTTP_RE = re.compile(r"HTTP\s+(\d+)")
RAW_SHA_RE = re.compile(r"SHA-256\s+([0-9a-f]{64})")
RAW_CANONICAL_RE = re.compile(r"canonical\s+(https://\S+?)(?:;|$)")
RECORDED_REASON_RE = re.compile(r"Reason:\s*([A-Z0-9_-]+)")
REPO = "https://github.com/ClaimBound/claimbound-evidence"
STATUS_LABELS = {
    "PASSED_UNDER_PROTOCOL": "Passed under protocol",
    "INSUFFICIENT_COVERAGE": "Insufficient coverage",
    "NEGATIVE_RESULT_UNDER_PROTOCOL": "Negative result under protocol",
    "BLOCKED_SOURCE": "Blocked source",
    "SOURCE_DRIFT": "Source drift",
}
REASON_LABELS = {
    "BLOCKED_HTTP_403": "Access policy / anti-bot (HTTP 403)",
    "BLOCKED_HTTP_404": "Not found / stale URL (HTTP 404)",
    "BLOCKED_HTTP_0": "Transport failed before an HTTP response",
    "BLOCKED_HTTP_444": "Server closed the request (HTTP 444)",
    "GATE_SPECIFIC_FACETS_MISSING": "Required gate-specific facts were absent",
    "GATE_FACETS_AND_EXECUTION_ARTIFACT_MISSING": "Required facts and an execution artifact were absent",
    "SOURCE_INTEGRITY_METADATA_INCOMPLETE": "Source-integrity metadata was incomplete",
    "SHELL_OR_TOPIC_MISMATCH": "The response was a shell, broad index, or topic mismatch",
    "EXECUTION_ARTIFACT_MISSING": "Independent execution artifact was absent",
    "LEGACY_GENERIC_GATE_EVIDENCE_MISSING": "Legacy review found incomplete gate evidence",
    "LEGACY_TOPIC_OR_GATE_DISCLOSURE_MISSING": "Topic- or gate-specific disclosure was absent",
    "SOURCE_BOUNDARY_DRIFT": "The frozen source boundary drifted",
    "PASSED_REVIEW": "Legacy review marked the gate as passed",
    "COMPLETE_TEXTUAL_GATE_FACETS": "Topic-specific textual gate facets were located",
    "SOURCE_BOUNDARY_VERIFIED": "Review marked the source boundary as verified",
}


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def load_cards() -> dict[str, tuple[Path, dict]]:
    found: dict[str, tuple[Path, dict]] = {}
    for path in sorted((ROOT / "docs/evidence_cards").glob("CLAIMBOUND-CB7K-*.json")):
        match = CARD_RE.search(path.name)
        if not match:
            continue
        protocol_id = match.group(1)
        if protocol_id in found:
            raise SystemExit(f"ERROR: duplicate evidence card for {protocol_id}")
        found[protocol_id] = (
            path,
            json.loads(path.read_text(encoding="utf-8")),
        )
    if len(found) != 7000:
        raise SystemExit(f"ERROR: expected 7000 CB7K cards, got {len(found)}")
    return found


def batch_issue(domain_number: int) -> int:
    return 166 + (domain_number - 1) // 3


def page(title: str, body: str, root: str = "") -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="ClaimBound CB7K recorded outcomes and protocol audit"><title>{esc(title)} · ClaimBound CB7K</title><style>
:root{{--ink:#172d31;--muted:#607276;--paper:#f3efe5;--card:#fffdf8;--line:#c9c2b4;--accent:#006d68;--pass:#217a55;--insufficient:#9a6500;--negative:#a33c35;--blocked:#675d8c;--drift:#9b4f78;--fail:#9b332d;--warn:#8c6100}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1280px;margin:auto;padding:30px 22px 80px}}a{{color:var(--accent)}}nav,.links,.filters{{display:flex;gap:14px;flex-wrap:wrap}}h1,h2,h3{{font-family:Georgia,serif}}h1{{font-size:clamp(36px,6vw,68px);line-height:1;max-width:1050px;margin:.45em 0}}h2{{line-height:1.15}}.lede{{font-size:19px;max-width:920px}}.note,.alert,.claim,.domain,.metric,.check{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px}}.alert{{border:2px solid var(--fail);background:#fff3ef}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.claims{{display:grid;gap:18px;margin-top:18px}}.claim h2{{margin:.55em 0 .25em}}.metric strong{{font:700 30px Georgia,serif;display:block}}.tag{{display:inline-block;padding:4px 9px;border-radius:99px;background:#e3ece8;margin:0 6px 6px 0;font-size:13px}}.status{{color:white}}.PASSED_UNDER_PROTOCOL{{background:var(--pass)}}.INSUFFICIENT_COVERAGE{{background:var(--insufficient)}}.NEGATIVE_RESULT_UNDER_PROTOCOL{{background:var(--negative)}}.BLOCKED_SOURCE{{background:var(--blocked)}}.SOURCE_DRIFT{{background:var(--drift)}}.PASS{{background:var(--pass);color:white}}.FAIL{{background:var(--fail);color:white}}.LIMITATION,.NOT_AUDITABLE{{background:var(--warn);color:white}}small,.muted{{color:var(--muted)}}blockquote{{margin:10px 0;border-left:4px solid var(--accent);padding:4px 0 4px 14px}}input,select{{padding:12px;border:1px solid var(--line);border-radius:9px;font:inherit;background:white}}input{{width:min(100%,520px)}}.filters{{margin:20px 0}}[hidden]{{display:none}}code,pre{{overflow-wrap:anywhere;white-space:pre-wrap}}details{{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}}summary{{cursor:pointer;font-weight:700}}dl{{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:7px 14px}}dt{{font-weight:700}}dd{{margin:0}}table{{width:100%;border-collapse:collapse;background:var(--card)}}th,td{{text-align:left;vertical-align:top;border:1px solid var(--line);padding:9px}}.table-wrap{{overflow-x:auto;margin:16px 0}}.claim-label{{font-weight:800;text-transform:uppercase;letter-spacing:.04em;font-size:13px}}@media(max-width:650px){{dl{{grid-template-columns:1fr}}dd{{margin-bottom:8px}}}}
</style></head><body><main><nav><a href="{root}index.html">All categories</a><a href="{root}audit/">Protocol audit</a><a href="{REPO}/issues/165">Campaign issue #165</a><a href="{REPO}">Repository</a></nav>{body}</main></body></html>'''


def fmt_mapping(value: object) -> str:
    if not value:
        return "Not recorded"
    return esc(json.dumps(value, ensure_ascii=False, sort_keys=True))


def raw_manifest_fields(card: dict) -> dict[str, object]:
    text = str(card.get("raw_payload_manifest", ""))
    http_match = RAW_HTTP_RE.search(text)
    sha_match = RAW_SHA_RE.search(text)
    canonical_match = RAW_CANONICAL_RE.search(text)
    return {
        "http_status": int(http_match.group(1)) if http_match else None,
        "source_sha256": sha_match.group(1) if sha_match else None,
        "canonical_url": canonical_match.group(1) if canonical_match else None,
    }


def reason_class_source(card: dict, review: dict) -> str:
    if card.get("result_status") == "BLOCKED_SOURCE":
        raw = raw_manifest_fields(card)
        suffix = (
            f"; manual-review HTTP is {review.get('http_status')}"
            if raw["http_status"] != review.get("http_status")
            else "; manual-review HTTP agrees"
        )
        return "Audit-derived from the card-recorded raw_payload_manifest observation" + suffix
    if card.get("result_status") == "SOURCE_DRIFT":
        return "Audit-derived from the recorded SOURCE_DRIFT outcome"
    if review.get("reason_code") or RECORDED_REASON_RE.search(
        str(card.get("manual_review", ""))
    ):
        return "Recorded as a structured or embedded Reason value"
    return "Audit-derived reproducible classification of legacy review text"


def audit_page(audit: dict) -> str:
    checks = "".join(
        f'''<article class="check"><span class="tag {esc(item['status'])}">{esc(item['status'])}</span><h2>{esc(item['label'])}</h2><p>{esc(item['finding'])}</p><p><strong>Measured:</strong> {esc(item['passed']) if item['passed'] is not None else 'not independently measurable'}{f" / {item['total']}" if item['total'] is not None else ''}</p></article>'''
        for item in audit["protocol_checks"]
    )
    reasons = audit["reason_counts"]
    blocked_codes = ["BLOCKED_HTTP_403", "BLOCKED_HTTP_404", "BLOCKED_HTTP_0", "BLOCKED_HTTP_444"]
    insufficient_codes = ["GATE_SPECIFIC_FACETS_MISSING", "GATE_FACETS_AND_EXECUTION_ARTIFACT_MISSING", "LEGACY_GENERIC_GATE_EVIDENCE_MISSING", "SOURCE_INTEGRITY_METADATA_INCOMPLETE", "SHELL_OR_TOPIC_MISMATCH", "LEGACY_TOPIC_OR_GATE_DISCLOSURE_MISSING", "EXECUTION_ARTIFACT_MISSING"]
    reason_rows = "".join(
        f"<tr><td>{esc(REASON_LABELS.get(code, code))}</td><td>{reasons.get(code,0):,}</td><td>{reasons.get(code,0)/audit['outcome_counts']['BLOCKED_SOURCE']*100:.2f}%</td></tr>"
        for code in blocked_codes
    ) + "".join(
        f"<tr><td>{esc(REASON_LABELS.get(code, code))}</td><td>{reasons.get(code,0):,}</td><td>{reasons.get(code,0)/audit['outcome_counts']['INSUFFICIENT_COVERAGE']*100:.2f}%</td></tr>"
        for code in insufficient_codes
    )
    gate_rows = "".join(
        f"<tr><td>{esc(gate)}</td><td>{counts.get('PASSED_UNDER_PROTOCOL',0)}</td><td>{counts.get('INSUFFICIENT_COVERAGE',0)}</td><td>{counts.get('BLOCKED_SOURCE',0)}</td><td>{counts.get('SOURCE_DRIFT',0)}</td></tr>"
        for gate, counts in audit["gate_result_counts"].items()
    )
    failing_domains = "".join(
        f"<tr><td>{esc(code)}</td><td><a href=\"../categories/{esc(item['slug'])}/\">{esc(item['title'])}</a></td><td>{item['distinct_source_urls']} / 7</td></tr>"
        for code, item in audit["domain_audit"].items()
        if not item["seven_distinct_topic_urls"]
    )
    reused = "".join(
        f"<tr><td><a href=\"{esc(item['url'])}\">{esc(item['url'])}</a></td><td>{item['topic_groups']}</td><td>{item['claim_count']}</td><td>{esc(item['result_counts'])}</td></tr>"
        for item in audit["topic_source_analysis"]["high_reuse_sources"][:12]
    )
    outcome = audit["outcome_counts"]
    topic_analysis = audit["topic_source_analysis"]
    manifest_summary = audit["current_manifest_summary"]
    blocked = outcome["BLOCKED_SOURCE"]
    insufficient = outcome["INSUFFICIENT_COVERAGE"]
    blocked_groups = topic_analysis["fully_blocked_groups"]
    drifted_groups = topic_analysis["fully_drifted_groups"]
    accessible_groups = topic_analysis["accessible_adjudicated_groups"]
    accessible_checks = accessible_groups * 10
    url_diversity_passes = sum(
        item["seven_distinct_topic_urls"] for item in audit["domain_audit"].values()
    )
    observed_errors = manifest_summary.get("observed_total_validator_errors")
    validator_error_text = (
        f"collectively produce {observed_errors:,} validation errors"
        if observed_errors is not None
        else f"collectively have at least {manifest_summary['minimum_campaign_validator_errors']:,} validation errors"
    )
    failing_batches = manifest_summary.get("failing_batches")
    batch_text = (
        f"{failing_batches} of 34 execution manifests fail"
        if failing_batches is not None
        else "Execution manifests fail"
    )
    return f'''<p>CLAIMBOUND / CAMPAIGN AUDIT</p><h1>Complete card set.<br>Protocol compliance not established.</h1><div class="alert"><strong>Critical interpretation.</strong> This campaign contains 7,000 generated topic × gate questions, not 7,000 captured verbatim public claims. The complete card set is present, but {batch_text} the current completion validator and {validator_error_text}. Schema/registry validation is a separate repository check. Do not describe this atlas as certification or as 7,000 independently verified factual claims.</div><h2>Why {blocked:,} cards are blocked</h2><p>There were {blocked_groups} inaccessible topic-source groups representing {topic_analysis['fully_blocked_unique_url_strings']} unique URL strings. Each group supplied one URL to ten gates, so every source-level access failure became ten cards. The card count therefore magnifies the underlying failed topic boundaries by exactly 10×. HTTP classes below come from each card-recorded raw-manifest observation; manual-review metadata differs on {audit['report_consistency']['blocked_http_mismatches']} blocked cards, but unpublished attempt history does not establish which observation came first.</p><h2>Why {insufficient:,} results are insufficient</h2><p>After excluding {blocked_groups} fully blocked and {drifted_groups} drifted topic-source groups, {accessible_groups} accessible topic-source groups remained. They produced {accessible_checks:,} gate checks; {insufficient:,} ({insufficient / accessible_checks * 100:.2f}%) lacked the required gate facts or executable evidence. Each topic-level selected URL was evaluated against ten gate roles, while none of the 7,000 execution entries records its expected source_role.</p><div class="table-wrap"><table><thead><tr><th>Root cause</th><th>Cards</th><th>Share within status</th></tr></thead><tbody>{reason_rows}</tbody></table></div><p><small>Structured reason codes are used where present. Another {audit['reason_methodology']['legacy_text_classifications']} legacy outcomes are reproducibly classified from unstructured review text; they were not originally stored as structured reason codes.</small></p><h2>Results by evidence gate</h2><div class="table-wrap"><table><thead><tr><th>Gate</th><th>Pass</th><th>Insufficient</th><th>Blocked</th><th>Drift</th></tr></thead><tbody>{gate_rows}</tbody></table></div><h2>Protocol rule audit</h2><section class="grid">{checks}</section><h2>Cross-topic source reuse</h2><p>{url_diversity_passes} of 100 domains record seven distinct topic URLs. The other {100-url_diversity_passes} domains use fewer; {topic_analysis['cross_topic_collision_slots']} topic slots participate in cross-topic URL collisions, including {topic_analysis['cross_topic_repeated_slots_beyond_first']} repeated assignments beyond the first occurrence. Distinctness alone does not prove independent pre-fetch selection.</p><div class="table-wrap"><table><thead><tr><th>Domain</th><th>Category</th><th>Distinct topic URLs</th></tr></thead><tbody>{failing_domains}</tbody></table></div><h2>Most reused URLs</h2><div class="table-wrap"><table><thead><tr><th>URL</th><th>Topics</th><th>Gate cards</th><th>Outcomes</th></tr></thead><tbody>{reused}</tbody></table></div><h2>Published-data inconsistencies</h2><p>The restored manual reports disagree with card raw-manifest metadata in {audit['report_consistency']['sha256_mismatches']} SHA-256 values, {audit['report_consistency']['http_mismatches']} HTTP statuses, and {audit['report_consistency']['canonical_url_mismatches']} canonical URLs. Selected source URLs and final outcome statuses otherwise match. Exact fetch-attempt history is not published, so the observation sequence cannot be independently reconstructed.</p><p class="links"><a href="protocol-audit.json">Download full audit JSON</a><a href="../results.json">Download all claim records</a></p>'''


def build(output: Path) -> None:
    ds = domains()
    candidates = {item["claim_id"]: item for item in make_claims(ds)}
    cards = load_cards()
    reviews = load_review_records()
    entries = load_execution_entries()
    audit = audit_campaign(run_validator=True)
    if set(cards) != set(candidates):
        raise SystemExit("ERROR: evidence cards do not exactly match the preregistered catalog")
    if set(reviews) != set(candidates) or set(entries) != set(candidates):
        raise SystemExit(
            "ERROR: detailed artifacts do not exactly cover the preregistered catalog "
            f"reviews={len(reviews)} manifests={len(entries)}"
        )
    checks_by_id = {item["id"]: item for item in audit["protocol_checks"]}
    if checks_by_id["report-file-integrity"]["status"] != "PASS":
        raise SystemExit("ERROR: a manual-review file does not match its evidence-card hash")
    validator_runs = audit["manifest_validator_runs"]
    if len(validator_runs) != 34:
        raise SystemExit("ERROR: expected current validator results for all 34 batches")
    batch_compliance = {
        item["issue"]: "PASS" if item["passed"] else "FAIL"
        for item in validator_runs
    }
    if output.exists():
        shutil.rmtree(output)
    (output / "categories").mkdir(parents=True)
    (output / "audit").mkdir()
    all_counts: Counter[str] = Counter()
    category_tiles: list[str] = []
    results: list[dict] = []
    for number, domain in enumerate(ds, 1):
        code = f"DOM{number:03d}"
        issue = batch_issue(number)
        batch_manifest_status = batch_compliance[issue]
        category_claims = [item for item in candidates.values() if item["domain_code"] == code]
        counts: Counter[str] = Counter()
        claim_html: list[str] = []
        for candidate in category_claims:
            claim_id = candidate["claim_id"]
            path, card = cards[claim_id]
            review = reviews[claim_id]
            entry = entries[claim_id]
            status = card["result_status"]
            if status not in STATUS_LABELS:
                raise SystemExit(f"ERROR: {claim_id} unknown status {status}")
            counts[status] += 1
            all_counts[status] += 1
            reason = reason_code(card, review)
            recorded_reason_match = RECORDED_REASON_RE.search(
                str(card.get("manual_review", ""))
            )
            recorded_reason = review.get("reason_code") or (
                recorded_reason_match.group(1) if recorded_reason_match else None
            )
            reason_origin = reason_class_source(card, review)
            raw_fields = raw_manifest_fields(card)
            mismatch_fields: list[str] = []
            for field in ("http_status", "source_sha256", "canonical_url"):
                if (
                    raw_fields[field] is not None
                    and review.get(field) is not None
                    and raw_fields[field] != review.get(field)
                ):
                    mismatch_fields.append(field)
            metadata_agreement = (
                "Mismatch: " + ", ".join(mismatch_fields)
                if mismatch_fields
                else "No mismatch in comparable card/report fields"
            )
            report_path = card["sanitized_report_path"]
            json_url = f"{REPO}/blob/main/{path.relative_to(ROOT).as_posix()}"
            svg_url = f"{REPO}/blob/main/{path.with_suffix('.svg').relative_to(ROOT).as_posix()}"
            report_url = f"{REPO}/blob/main/{report_path}"
            manifest_url = f"{REPO}/blob/main/artifacts/claim_batch_{issue}_execution_manifest.json"
            missing_facets = review.get("missing_facets", [])
            source_claim_note = (
                "NOT RECORDED — there is no dedicated field binding a concrete factual "
                "source assertion as the claim under test. A target statement or locator "
                "may contain a generated boundary or supporting excerpt, but it is not an "
                "explicitly frozen claim-under-test field."
            )
            target_statement = review.get("target_statement")
            manifest_source_role = entry.get("source_role")
            search_text = " ".join([claim_id, candidate["topic"], candidate["gate"], status, reason, candidate["frozen_candidate_claim"], card["official_source_url"]]).lower()
            claim_html.append(
                f'''<article class="claim" data-search="{esc(search_text)}" data-status="{esc(status)}">
<span class="tag">{esc(claim_id)}</span><span class="tag">{esc(candidate['gate'])}</span><span class="tag status {esc(status)}">{esc(STATUS_LABELS[status])}</span>
<h2>{esc(candidate['topic'])}</h2>
<p class="claim-label">Exact preregistered audit question</p><blockquote>{esc(candidate['frozen_candidate_claim'])}</blockquote>
<p><strong>Dedicated concrete claim-under-test:</strong> {esc(source_claim_note)}</p>
<dl>
<dt>Review target statement</dt><dd>{esc(target_statement or 'Not recorded')}</dd>
<dt>Decision rule</dt><dd>{esc(candidate['adjudication_rule'])}</dd>
<dt>Expected method</dt><dd><code>{esc(GATE_METHODS[candidate['gate']])}</code></dd>
<dt>Expected source role</dt><dd><code>{esc(GATE_SOURCE_ROLES[candidate['gate']])}</code></dd>
<dt>Manifest source role</dt><dd><code>{esc(manifest_source_role or 'Not recorded')}</code></dd>
<dt>Recorded reason code</dt><dd><code>{esc(recorded_reason or 'Not recorded')}</code></dd>
<dt>Audit reason class</dt><dd><code>{esc(reason)}</code> — {esc(REASON_LABELS.get(reason, reason))}</dd>
<dt>Reason-class source</dt><dd>{esc(reason_origin)}</dd>
<dt>Review basis</dt><dd>{esc(review.get('review_basis') or card.get('manual_review'))}</dd>
<dt>Missing facets</dt><dd>{esc(', '.join(missing_facets) if missing_facets else 'None recorded')}</dd>
<dt>Evidence locator / supporting excerpt</dt><dd>{esc(review.get('locator') or card.get('manual_review'))}</dd>
<dt>Extraction</dt><dd>{esc(review.get('extraction_quality') or 'Not recorded')}</dd>
<dt>Result boundary</dt><dd>{esc(card.get('claim_boundary'))}</dd>
</dl>
<details open><summary>Source and attempt metadata</summary><dl>
<dt>Selected URL</dt><dd><a href="{esc(card['official_source_url'])}">{esc(card['official_source_name'])}</a></dd>
<dt>Manual-review canonical URL</dt><dd>{esc(review.get('canonical_url') or 'Not recorded')}</dd>
<dt>Manual-review HTTP status</dt><dd>{esc(review.get('http_status'))}</dd>
<dt>Manual-review source SHA-256</dt><dd><code>{esc(review.get('source_sha256'))}</code></dd>
<dt>Card raw-manifest canonical URL</dt><dd>{esc(raw_fields['canonical_url'] or 'Not recorded')}</dd>
<dt>Card raw-manifest HTTP status</dt><dd>{esc(raw_fields['http_status'])}</dd>
<dt>Card raw-manifest source SHA-256</dt><dd><code>{esc(raw_fields['source_sha256'])}</code></dd>
<dt>Card/report metadata agreement</dt><dd>{esc(metadata_agreement)}</dd>
<dt>Access date</dt><dd>{esc(card.get('access_date'))}; exact timestamp and redirect chain are not published</dd>
<dt>Raw manifest summary</dt><dd>{esc(card.get('raw_payload_manifest'))}</dd>
<dt>Raw payload committed</dt><dd>{esc(card.get('raw_payload_committed'))}</dd>
<dt>Source-rights note</dt><dd>{esc(card.get('source_rights_note'))}</dd>
</dl></details>
<details><summary>Protocol, execution, and reproducibility</summary><dl>
<dt>Frozen parameters field</dt><dd><code>{fmt_mapping(entry.get('frozen_parameters'))}</code></dd>
<dt>Support rule field</dt><dd>{esc(entry.get('support_rule'))}</dd>
<dt>Negative rule field</dt><dd>{esc(entry.get('negative_rule'))}</dd>
<dt>Selection provenance</dt><dd>{fmt_mapping(entry.get('selection_provenance'))}</dd>
<dt>Current batch-manifest audit</dt><dd><strong>{batch_manifest_status}</strong></dd>
<dt>Protocol version</dt><dd>{esc(card.get('protocol_version'))}</dd>
<dt>Verification</dt><dd>{esc(card.get('verification_level'))} ({esc(card.get('verification_count'))}); {esc(card.get('reproduction_level'))}</dd>
<dt>Execution</dt><dd>{esc(card.get('execution_mode'))}; AI assistance: {esc(card.get('ai_assistance'))}</dd>
<dt>Operator</dt><dd>{esc(card.get('operator'))}</dd>
<dt>Runner command</dt><dd><code>{esc(card.get('runner_command'))}</code></dd>
<dt>Recorded git commit</dt><dd><code>{esc(card.get('git_commit'))}</code></dd>
<dt>Created / last verified</dt><dd>{esc(card.get('created_at'))} / {esc(card.get('last_verified_date'))}</dd>
<dt>Sanitized report SHA-256</dt><dd><code>{esc(card.get('sanitized_report_sha256'))}</code></dd>
<dt>Limitations</dt><dd>{esc('; '.join(card.get('known_limitations', [])))}</dd>
</dl><p class="links"><a href="{json_url}">Evidence JSON</a><a href="{svg_url}">Rendered card</a><a href="{report_url}">Manual-review report</a><a href="{manifest_url}">Execution manifest</a></p></details>
</article>'''
            )
            results.append({
                "claim_id": claim_id,
                "category": domain["slug"],
                "topic": candidate["topic"],
                "gate": candidate["gate"],
                "exact_preregistered_audit_question": candidate["frozen_candidate_claim"],
                "dedicated_concrete_claim_under_test": None,
                "dedicated_claim_gap": source_claim_note,
                "review_target_statement": target_statement,
                "adjudication_rule": candidate["adjudication_rule"],
                "expected_evaluation_method": GATE_METHODS[candidate["gate"]],
                "expected_source_role": GATE_SOURCE_ROLES[candidate["gate"]],
                "manifest_source_role": manifest_source_role,
                "result_status": status,
                "recorded_reason_code": recorded_reason,
                "audit_reason_class": reason,
                "reason_class_source": reason_origin,
                "review_basis": review.get("review_basis"),
                "missing_facets": missing_facets,
                "evidence_locator": review.get("locator"),
                "extraction_quality": review.get("extraction_quality"),
                "claim_boundary": card.get("claim_boundary"),
                "selected_source_url": card.get("official_source_url"),
                "manual_review_canonical_url": review.get("canonical_url"),
                "manual_review_http_status": review.get("http_status"),
                "manual_review_source_sha256": review.get("source_sha256"),
                "card_raw_manifest_canonical_url": raw_fields["canonical_url"],
                "card_raw_manifest_http_status": raw_fields["http_status"],
                "card_raw_manifest_source_sha256": raw_fields["source_sha256"],
                "card_report_metadata_mismatches": mismatch_fields,
                "access_date": card.get("access_date"),
                "raw_payload_manifest": card.get("raw_payload_manifest"),
                "raw_payload_committed": card.get("raw_payload_committed"),
                "source_rights_note": card.get("source_rights_note"),
                "frozen_parameters": entry.get("frozen_parameters"),
                "support_rule": entry.get("support_rule"),
                "negative_rule": entry.get("negative_rule"),
                "selection_provenance": entry.get("selection_provenance"),
                "protocol_version": card.get("protocol_version"),
                "verification_level": card.get("verification_level"),
                "verification_count": card.get("verification_count"),
                "reproduction_level": card.get("reproduction_level"),
                "execution_mode": card.get("execution_mode"),
                "ai_assistance": card.get("ai_assistance"),
                "operator": card.get("operator"),
                "runner_command": card.get("runner_command"),
                "recorded_git_commit": card.get("git_commit"),
                "created_at": card.get("created_at"),
                "last_verified_date": card.get("last_verified_date"),
                "sanitized_report_sha256": card.get("sanitized_report_sha256"),
                "source_frozen_sha256": review.get("source_frozen_sha256"),
                "evidence_card": path.relative_to(ROOT).as_posix(),
                "manual_review_report": report_path,
                "current_batch_manifest_compliance": batch_manifest_status,
            })
        summary = "".join(
            f'<div class="metric"><strong>{counts.get(status,0)}</strong><span>{esc(label)}</span></div>'
            for status, label in STATUS_LABELS.items()
        )
        domain_audit = audit["domain_audit"][code]
        url_diversity = "PASS" if domain_audit["seven_distinct_topic_urls"] else "FAIL"
        category_reason_rows = "".join(
            f"<tr><td><code>{esc(reason_name)}</code></td><td>{esc(REASON_LABELS.get(reason_name, reason_name))}</td><td>{reason_count}</td></tr>"
            for reason_name, reason_count in sorted(domain_audit["reason_counts"].items())
        )
        category_body = f'''<p>CLAIMBOUND / RECORDED CATEGORY {code}</p><h1>{esc(domain['title'])}</h1><div class="alert"><strong>What these records are.</strong> Seventy preregistered topic × gate questions were evaluated. No record has a dedicated field binding a concrete factual source assertion as the claim under test. Supporting excerpts or generated target statements are shown separately and are not silently promoted into claims.</div><p><a href="{REPO}/issues/{issue}">Batch issue #{issue}</a> · Maintainer publication · Current batch-manifest audit: <strong>{batch_manifest_status}</strong> · Distinct-topic-URL check: <strong>{url_diversity}</strong> ({domain_audit['distinct_source_urls']}/7 URLs; distinctness does not prove pre-fetch independence)</p><section class="grid">{summary}</section><h2>Reason-class summary for this category</h2><div class="table-wrap"><table><thead><tr><th>Audit reason class</th><th>Meaning</th><th>Cards</th></tr></thead><tbody>{category_reason_rows}</tbody></table></div><p><small>Each card below identifies whether its reason class was recorded or audit-derived from a card manifest or legacy review text.</small></p><div class="filters"><input id="q" type="search" placeholder="Search exact questions, topics, gates, reasons, or URLs" aria-label="Search checks"><select id="status" aria-label="Filter by result"><option value="">All results</option>{''.join(f'<option value="{key}">{esc(label)}</option>' for key,label in STATUS_LABELS.items())}</select></div><section class="claims">{''.join(claim_html)}</section><script>const q=document.querySelector('#q'),s=document.querySelector('#status'),items=[...document.querySelectorAll('.claim')];function filter(){{const text=q.value.toLowerCase();items.forEach(x=>x.hidden=!(x.dataset.search.includes(text)&&(!s.value||x.dataset.status===s.value)))}}q.oninput=filter;s.onchange=filter;</script>'''
        category_dir = output / "categories" / domain["slug"]
        category_dir.mkdir()
        (category_dir / "index.html").write_text(
            page(domain["title"], category_body, "../../"), encoding="utf-8"
        )
        count_text = " · ".join(
            f"{counts.get(status,0)} {label.lower()}"
            for status, label in STATUS_LABELS.items()
            if counts.get(status)
        )
        category_tiles.append(f'''<article class="domain" data-search="{esc((domain['title']+' '+domain['slug']+' '+' '.join(domain['topics'])).lower())}"><p><small>{code} · issue #{issue} · URL diversity {url_diversity} · manifest {batch_manifest_status}</small></p><h2><a href="categories/{esc(domain['slug'])}/">{esc(domain['title'])}</a></h2><p>70 gate checks · {esc(count_text)}</p></article>''')

    metrics = "".join(
        f'<div class="metric"><strong>{all_counts.get(status,0)}</strong><span>{esc(label)}</span></div>'
        for status, label in STATUS_LABELS.items()
    )
    failing_batches = audit["current_manifest_summary"]["failing_batches"]
    manifest_sentence = (
        f"{failing_batches} of 34 execution manifests fail"
        if failing_batches is not None
        else "Execution manifests fail"
    )
    home = f'''<p>CLAIMBOUND / RECORDED OUTCOMES + PROTOCOL AUDIT</p><h1>7,000 topic × gate checks.<br>Not 7,000 captured public claims.</h1><div class="alert"><strong>Audit correction.</strong> The original atlas called these “verified public claims.” That was too broad. The catalog mechanically generated ten audit questions for each of 700 topics and has no dedicated field binding a concrete source assertion, number, headline, or quotation as the claim under test. {manifest_sentence} the current ClaimBound completion validator. The records remain published below with their exact scope and failures visible.</div><p class="lede">There are 100 category routes with 70 records each. Every record now exposes the exact preregistered question, target statement when present, decision rule, expected and recorded source-role fields, recorded and audit-derived reason classes, locator, card-versus-review fetch metadata, protocol fields, report, manifest, operator, runner, and reproducibility status.</p><section class="grid" style="margin:18px 0">{metrics}</section><p class="links"><a href="audit/">Read the full protocol audit</a><a href="results.json">Download all detailed records</a><a href="audit/protocol-audit.json">Download audit JSON</a><a href="{REPO}/issues/165">Master issue #165</a></p><div class="filters"><input id="q" type="search" placeholder="Filter 100 categories" aria-label="Filter categories"></div><section class="grid">{''.join(category_tiles)}</section><script>const q=document.querySelector('#q');q.oninput=()=>document.querySelectorAll('.domain').forEach(x=>x.hidden=!x.dataset.search.includes(q.value.toLowerCase()))</script>'''
    (output / "index.html").write_text(
        page("7,000 recorded topic-gate checks", home), encoding="utf-8"
    )
    (output / "results.json").write_text(
        json.dumps(
            {
                "maintainer": "NeoZorK",
                "campaign_issue": 165,
                "publication_boundary": "Recorded topic × gate outcomes; not 7,000 captured verbatim public claims",
                "protocol_audit_conclusion": audit["conclusion"],
                "category_count": 100,
                "claim_count": 7000,
                "result_counts": {
                    status: all_counts.get(status, 0) for status in STATUS_LABELS
                },
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "audit" / "index.html").write_text(
        page("CB7K protocol audit", audit_page(audit), "../"), encoding="utf-8"
    )
    (output / "audit" / "protocol-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")
    print(
        f"Built {len(results)} detailed records across {len(ds)} category pages: {dict(all_counts)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("tmp/verified-claim-atlas")
    )
    args = parser.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
