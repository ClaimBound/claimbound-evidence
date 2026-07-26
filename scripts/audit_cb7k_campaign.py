#!/usr/bin/env python3
"""Audit the complete CB7K campaign without re-adjudicating its outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_public_claim_catalog import (
    GATE_METHODS,
    GATE_SOURCE_ROLES,
    OUTCOMES,
    ROOT,
    domains,
    make_claims,
)

CARD_RE = re.compile(
    r"CLAIMBOUND-(CB7K-DOM\d{3}-T\d{2}-G\d{2})-\d{4}-\d{2}-\d{2}\.json$"
)
REASON_RE = re.compile(r"Reason:\s*([A-Z0-9_-]+)")
HTTP_RE = re.compile(r"HTTP\s+(\d+)")
SHA_RE = re.compile(r"SHA-256\s+([0-9a-f]{64})")
CANONICAL_RE = re.compile(r"canonical\s+(https://\S+?)(?:;|$)")


def load_cards() -> dict[str, tuple[Path, dict[str, Any]]]:
    result: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted((ROOT / "docs/evidence_cards").glob("CLAIMBOUND-CB7K-*.json")):
        match = CARD_RE.search(path.name)
        if match:
            claim_id = match.group(1)
            if claim_id in result:
                raise SystemExit(f"ERROR: duplicate evidence card for {claim_id}")
            result[claim_id] = (path, json.loads(path.read_text(encoding="utf-8")))
    return result


def load_review_records() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for issue in range(166, 200):
        paths = sorted((ROOT / "artifacts").glob(f"claim_batch_{issue}*_manual_review.json"))
        if not paths:
            continue
        payload = json.loads(paths[-1].read_text(encoding="utf-8"))
        for record in payload.get("cards", []):
            claim_id = record["claim_id"]
            if claim_id in result:
                raise SystemExit(f"ERROR: duplicate manual-review row for {claim_id}")
            result[claim_id] = record
    return result


def load_execution_entries() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for issue in range(166, 200):
        path = ROOT / "artifacts" / f"claim_batch_{issue}_execution_manifest.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload.get("entries", []):
            claim_id = record["claim_id"]
            if claim_id in result:
                raise SystemExit(f"ERROR: duplicate execution-manifest row for {claim_id}")
            result[claim_id] = record
    return result


def reason_code(card: dict[str, Any], review: dict[str, Any] | None = None) -> str:
    status = card["result_status"]
    text = card.get("manual_review", "")
    if status == "BLOCKED_SOURCE":
        match = HTTP_RE.search(card.get("raw_payload_manifest", ""))
        return f"BLOCKED_HTTP_{match.group(1)}" if match else "BLOCKED_TRANSPORT_UNKNOWN"
    if status == "SOURCE_DRIFT":
        return "SOURCE_BOUNDARY_DRIFT"
    if review and review.get("reason_code"):
        code = str(review["reason_code"])
        return "SHELL_OR_TOPIC_MISMATCH" if code == "VERY_SHORT_OR_SHELL_EXTRACTION" else code
    if status == "PASSED_UNDER_PROTOCOL":
        match = REASON_RE.search(text)
        return match.group(1) if match else "PASSED_REVIEW"
    match = REASON_RE.search(text)
    if match:
        code = match.group(1)
        if code == "VERY_SHORT_OR_SHELL_EXTRACTION":
            return "SHELL_OR_TOPIC_MISMATCH"
        return code
    if text.startswith("The frozen source was reviewed but did not expose"):
        return "LEGACY_GENERIC_GATE_EVIDENCE_MISSING"
    if "shell" in text.lower() or "broad index" in text.lower():
        return "SHELL_OR_TOPIC_MISMATCH"
    return "LEGACY_TOPIC_OR_GATE_DISCLOSURE_MISSING"


def _check(
    check_id: str,
    label: str,
    status: str,
    passed: int | None,
    total: int | None,
    finding: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "passed": passed,
        "total": total,
        "finding": finding,
    }


def audit_campaign(run_validator: bool = False) -> dict[str, Any]:
    candidate_rows = make_claims(domains())
    candidates = {item["claim_id"]: item for item in candidate_rows}
    if len(candidate_rows) != len(candidates):
        raise SystemExit("ERROR: duplicate preregistered claim IDs")
    cards = load_cards()
    reviews = load_review_records()
    entries = load_execution_entries()
    status_counts = Counter(card["result_status"] for _, card in cards.values())
    outcome_counts = {outcome: status_counts[outcome] for outcome in OUTCOMES}
    cause_counts = Counter(
        reason_code(card, reviews.get(claim_id))
        for claim_id, (_, card) in cards.items()
    )
    by_gate: dict[str, Counter[str]] = defaultdict(Counter)
    by_domain: dict[str, dict[str, Any]] = {}
    topic_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim_id, (_, card) in cards.items():
        candidate = candidates.get(claim_id, {})
        by_gate[candidate.get("gate", "UNKNOWN")][card["result_status"]] += 1
        topic_groups[claim_id.rsplit("-G", 1)[0]].append(card)
    for index, domain in enumerate(domains(), 1):
        code = f"DOM{index:03d}"
        scoped = [
            (claim_id, card)
            for claim_id, (_, card) in cards.items()
            if claim_id.startswith(f"CB7K-{code}-")
        ]
        urls = {card["official_source_url"] for _, card in scoped}
        by_domain[code] = {
            "slug": domain["slug"],
            "title": domain["title"],
            "claim_count": len(scoped),
            "distinct_source_urls": len(urls),
            "seven_distinct_topic_urls": len(urls) >= 7,
            "result_counts": dict(Counter(card["result_status"] for _, card in scoped)),
            "reason_counts": dict(
                Counter(reason_code(card, reviews.get(claim_id)) for claim_id, card in scoped)
            ),
        }

    manifest_methods = sum(
        entry.get("evaluation_method") == GATE_METHODS[candidates[claim_id]["gate"]]
        for claim_id, entry in entries.items()
        if claim_id in candidates
    )
    manifest_rules = sum(
        bool(entry.get("support_rule")) and bool(entry.get("negative_rule"))
        for entry in entries.values()
    )
    manifest_url_matches = sum(
        entry.get("source_url") == cards[claim_id][1].get("official_source_url")
        for claim_id, entry in entries.items()
        if claim_id in cards
    )
    source_roles = sum(
        entry.get("source_role") == GATE_SOURCE_ROLES[candidates[claim_id]["gate"]]
        for claim_id, entry in entries.items()
        if claim_id in candidates
    )
    def valid_selection_provenance(entry: dict[str, Any]) -> bool:
        provenance = entry.get("selection_provenance")
        return (
            isinstance(provenance, dict)
            and str(provenance.get("discovery_url", "")).startswith("https://")
            and provenance.get("selected_before_evaluation") is True
            and provenance.get("discovery_http_status") == 200
            and re.fullmatch(
                r"[0-9a-f]{64}", str(provenance.get("discovery_sha256", ""))
            )
            is not None
            and len(str(provenance.get("source_role_locator", "")).strip()) >= 20
        )

    selection_provenance = sum(
        valid_selection_provenance(entry) for entry in entries.values()
    )
    domain_url_passes = sum(
        value["seven_distinct_topic_urls"] for value in by_domain.values()
    )
    http_status_counts = Counter()
    review_http_status_counts = Counter(
        str(review.get("http_status")) for review in reviews.values()
    )
    sha_manifest_count = 0
    for _, card in cards.values():
        match = HTTP_RE.search(card.get("raw_payload_manifest", ""))
        http_status_counts[match.group(1) if match else "UNKNOWN"] += 1
        sha_manifest_count += bool(SHA_RE.search(card.get("raw_payload_manifest", "")))

    report_status_mismatches = 0
    report_http_mismatches = 0
    report_http_comparable = 0
    report_sha_mismatches = 0
    report_sha_comparable = 0
    report_url_mismatches = 0
    report_url_comparable = 0
    report_canonical_mismatches = 0
    report_canonical_comparable = 0
    blocked_report_http_mismatches = 0
    report_file_hash_matches = 0
    report_hash_cache: dict[Path, str] = {}
    for claim_id, review in reviews.items():
        if claim_id not in cards:
            continue
        card = cards[claim_id][1]
        report_status_mismatches += review.get("status") != card.get("result_status")
        card_http = HTTP_RE.search(card.get("raw_payload_manifest", ""))
        if card_http and review.get("http_status") is not None:
            report_http_comparable += 1
            http_mismatch = int(card_http.group(1)) != int(review["http_status"])
            report_http_mismatches += http_mismatch
            blocked_report_http_mismatches += (
                http_mismatch and card.get("result_status") == "BLOCKED_SOURCE"
            )
        card_sha = SHA_RE.search(card.get("raw_payload_manifest", ""))
        if card_sha and review.get("source_sha256"):
            report_sha_comparable += 1
            report_sha_mismatches += card_sha.group(1) != review["source_sha256"]
        if review.get("source_url"):
            report_url_comparable += 1
            report_url_mismatches += review["source_url"] != card.get("official_source_url")
        card_canonical = CANONICAL_RE.search(card.get("raw_payload_manifest", ""))
        if card_canonical and review.get("canonical_url"):
            report_canonical_comparable += 1
            report_canonical_mismatches += card_canonical.group(1) != review["canonical_url"]
        report_path = ROOT / str(card.get("sanitized_report_path", ""))
        if report_path.is_file():
            if report_path not in report_hash_cache:
                report_hash_cache[report_path] = hashlib.sha256(
                    report_path.read_bytes()
                ).hexdigest()
            report_file_hash_matches += (
                report_hash_cache[report_path] == card.get("sanitized_report_sha256")
            )

    source_manifest_declared = 0
    source_manifest_present = 0
    source_manifest_hash_matches = 0
    for issue in range(166, 200):
        execution_path = ROOT / "artifacts" / f"claim_batch_{issue}_execution_manifest.json"
        execution_payload = json.loads(execution_path.read_text(encoding="utf-8"))
        expected_hash = execution_payload.get("source_manifest_sha256")
        source_manifest_declared += bool(expected_hash)
        source_path = ROOT / "artifacts" / f"claim_batch_{issue}_source_manifest.json"
        if not source_path.is_file():
            continue
        source_manifest_present += 1
        source_manifest_hash_matches += (
            bool(expected_hash)
            and hashlib.sha256(source_path.read_bytes()).hexdigest() == expected_hash
        )

    executable_gates = {"numerator-denominator", "method-version", "reproducibility"}
    executable_passes = sum(
        card.get("result_status") == "PASSED_UNDER_PROTOCOL"
        and candidates[claim_id]["gate"] in executable_gates
        for claim_id, (_, card) in cards.items()
    )
    independently_reproduced_executable_passes = sum(
        card.get("result_status") == "PASSED_UNDER_PROTOCOL"
        and candidates[claim_id]["gate"] in executable_gates
        and card.get("reproduction_level") != "not independently reproduced"
        for claim_id, (_, card) in cards.items()
    )
    reproducibility_passes = sum(
        card.get("result_status") == "PASSED_UNDER_PROTOCOL"
        and candidates[claim_id]["gate"] == "reproducibility"
        for claim_id, (_, card) in cards.items()
    )
    git_commit_values = {str(card.get("git_commit", "")) for _, card in cards.values()}
    resolvable_git_commits: set[str] = set()
    for value in git_commit_values:
        if re.fullmatch(r"[0-9a-f]{7,40}", value) is None:
            continue
        process = subprocess.run(
            ["git", "cat-file", "-e", f"{value}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if process.returncode == 0:
            resolvable_git_commits.add(value)
    valid_git_commits = sum(
        str(card.get("git_commit", "")) in resolvable_git_commits
        for _, card in cards.values()
    )
    source_frozen_hashes = sum(
        bool(review.get("source_frozen_sha256")) for review in reviews.values()
    )
    exact_access_timestamps = sum(
        bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T.+", str(card.get("access_date", ""))))
        for _, card in cards.values()
    )
    recorded_redirect_chains = sum(
        isinstance(review.get("redirect_chain"), list) for review in reviews.values()
    )
    source_integrity_passes = sum(
        card.get("result_status") == "PASSED_UNDER_PROTOCOL"
        and candidates[claim_id]["gate"] == "source-integrity"
        for claim_id, (_, card) in cards.items()
    )
    published_source_manifests = len(
        list((ROOT / "artifacts").glob("claim_batch_*_source_manifest.json"))
    )
    runner_paths_present = 0
    for _, card in cards.values():
        command = str(card.get("runner_command", "")).split()
        runner_paths_present += (
            len(command) >= 2 and (ROOT / command[1]).is_file()
        )
    maintainer_operator = sum(
        card.get("operator") == "NeoZorK" for _, card in cards.values()
    )
    topic_url_counts = Counter(
        group[0]["official_source_url"] for group in topic_groups.values() if group
    )
    high_reuse_sources = []
    for url, group_count in topic_url_counts.most_common(20):
        if group_count < 2:
            continue
        scoped = [card for group in topic_groups.values() for card in group if card["official_source_url"] == url]
        high_reuse_sources.append({"url": url, "topic_groups": group_count, "claim_count": len(scoped), "result_counts": dict(Counter(card["result_status"] for card in scoped))})
    cross_topic_reuse_slots = 0
    cross_topic_repeated_slots = 0
    for domain in by_domain.values():
        code = next(key for key, value in by_domain.items() if value is domain)
        topic_urls = []
        for topic in range(1, 8):
            prefix = f"CB7K-{code}-T{topic:02d}-"
            topic_urls.append(next(card["official_source_url"] for claim_id, (_, card) in cards.items() if claim_id.startswith(prefix)))
        counts = Counter(topic_urls)
        cross_topic_reuse_slots += sum(count for count in counts.values() if count > 1)
        cross_topic_repeated_slots += sum(count - 1 for count in counts.values() if count > 1)

    fully_blocked_groups = [
        group
        for group in topic_groups.values()
        if all(card["result_status"] == "BLOCKED_SOURCE" for card in group)
    ]
    blocked_unique_urls = len(
        {group[0]["official_source_url"] for group in fully_blocked_groups}
    )

    issue_counts: dict[int, Counter[str]] = defaultdict(Counter)
    for claim_id, (_, card) in cards.items():
        issue = 166 + (int(claim_id.split("-DOM", 1)[1].split("-", 1)[0]) - 1) // 3
        issue_counts[issue][card["result_status"]] += 1
    cohort_specs = {
        "issues_166_171": range(166, 172),
        "issues_172_184": range(172, 185),
        "issues_185_199": range(185, 200),
    }
    cohort_counts = {
        name: dict(sum((issue_counts[issue] for issue in issues), Counter()))
        for name, issues in cohort_specs.items()
    }

    checks = [
        _check("complete-card-set", "Exactly one evidence card per preregistered question", "PASS" if len(cards) == 7000 and set(cards) == set(candidates) else "FAIL", len(set(cards) & set(candidates)), 7000, f"Found {len(cards)} unique CB7K cards for {len(candidates)} preregistered questions; duplicate IDs are rejected while loading."),
        _check("allowed-outcomes", "All observed outcome values belong to the allowed enum", "PASS" if set(status_counts) <= set(OUTCOMES) else "FAIL", sum(status_counts[value] for value in OUTCOMES), 7000, f"Observed outcomes: {outcome_counts}. This check does not establish historical retention or absence of rewriting."),
        _check("raw-payload-policy", "Cards record raw_payload_committed=false", "PASS" if all(card.get("raw_payload_committed") is False for _, card in cards.values()) else "FAIL", sum(card.get("raw_payload_committed") is False for _, card in cards.values()), 7000, "All cards carry the false flag. This field-level check does not independently prove local retention or exhaustively classify every repository file."),
        _check("https-source", "The recorded source URL syntactically starts with https://", "PASS" if all(str(card.get("official_source_url", "")).startswith("https://") for _, card in cards.values()) else "FAIL", sum(str(card.get("official_source_url", "")).startswith("https://") for _, card in cards.values()), 7000, f"{len({card['official_source_url'] for _, card in cards.values()})} distinct URL strings are recorded; this check does not establish public accessibility, exactness, or freeze timing."),
        _check("response-hash", "A response SHA-256 is recorded", "PASS" if sha_manifest_count == 7000 else "FAIL", sha_manifest_count, 7000, "This proves a hash was recorded, not that the private raw bytes still reproduce it."),
        _check("manifest-completeness", "Execution manifests exactly cover the preregistered claim set", "PASS" if set(entries) == set(candidates) else "FAIL", len(set(entries) & set(candidates)), 7000, f"Loaded {len(entries)} unique execution entries; missing={len(set(candidates)-set(entries))}, extra={len(set(entries)-set(candidates))}."),
        _check("manifest-method", "Execution manifest records the expected gate-specific method", "PASS" if manifest_methods == 7000 else "FAIL", manifest_methods, 7000, "Compared each execution entry with the current gate-to-method mapping; missing timestamped provenance means pre-fetch freezing is not proven."),
        _check("support-negative-rules", "Execution manifest contains support and negative rule fields", "PASS" if manifest_rules == 7000 else "FAIL", manifest_rules, 7000, "Every execution entry contains non-empty support_rule and negative_rule; their presence does not prove when they were frozen."),
        _check("manifest-card-url", "Manifest source URL equals final card source URL", "PASS" if manifest_url_matches == 7000 else "FAIL", manifest_url_matches, 7000, "End-state equality supports no-substitution consistency, but does not independently prove selection occurred before the first fetch."),
        _check("topic-url-diversity", "Each domain records at least seven distinct topic URLs", "PASS" if domain_url_passes == 100 else "FAIL", domain_url_passes, 100, f"{100-domain_url_passes} domains reuse a URL across different topics. The other {domain_url_passes} pass this syntactic diversity check only; pre-fetch independence is not established."),
        _check("source-role", "Every gate records its required source role", "PASS" if source_roles == 7000 else "FAIL", source_roles, 7000, "The execution manifests predate the current source_role requirement and do not satisfy it."),
        _check("selection-provenance", "Discovery and pre-evaluation source selection are auditable", "PASS" if selection_provenance == 7000 else "FAIL", selection_provenance, 7000, "No execution entry contains current selection_provenance with selected_before_evaluation=true, discovery HTTP 200, discovery hash, and role locator."),
        _check("source-frozen-hash", "The review record publishes source_frozen_sha256", "PASS" if source_frozen_hashes == 7000 else "FAIL", source_frozen_hashes, 7000, "All published review rows leave source_frozen_sha256 null; a separate source_sha256 is recorded, but the null field does not establish whether or when a private pre-fetch freeze occurred."),
        _check("fetch-attempt-provenance", "Exact access timestamp and redirect chain are published", "PASS" if exact_access_timestamps == 7000 and recorded_redirect_chains == 7000 else "FAIL", min(exact_access_timestamps, recorded_redirect_chains), 7000, f"Cards record a date only, manual reports contain no redirect_chain field, and only {published_source_manifests} of 34 source manifests are published; those manifests contain source URLs but no fetch attempts."),
        _check("source-integrity-pass-evidence", "Source-integrity passes expose the metadata required by their own question", "FAIL" if source_integrity_passes else "PASS", 0, source_integrity_passes, f"{source_integrity_passes} source-integrity checks are marked passed even though exact access timestamps and redirect chains are not published."),
        _check("card-git-commit", "Evidence cards reference a resolvable git commit object", "PASS" if valid_git_commits == 7000 else "FAIL", valid_git_commits, 7000, "Cards contain placeholders such as local-before-merge; candidate hex values, if any, are resolved with git cat-file rather than accepted by shape alone."),
        _check("concrete-source-claim", "A dedicated concrete claim-under-test is captured", "FAIL", 0, 7000, "The catalog stores generated topic × gate questions and no dedicated claim-under-test field. Some evidence locators contain supporting excerpts, but those excerpts are not explicitly frozen as the claim being checked."),
        _check("runner-availability", "The recorded runner command points to a published script", "PASS" if runner_paths_present == 7000 else "FAIL", runner_paths_present, 7000, f"{7000-runner_paths_present} cards still point to an unavailable historical runner."),
        _check("maintainer-operator", "The human maintainer is named as the card operator", "PASS" if maintainer_operator == 7000 else "FAIL", maintainer_operator, 7000, f"{7000-maintainer_operator} cards name ClaimBound rather than the NeoZorK maintainer handle."),
        _check("executable-pass-reproduction", "Passes in execution-required gates were independently reproduced", "PASS" if independently_reproduced_executable_passes == executable_passes else "FAIL", independently_reproduced_executable_passes, executable_passes, f"{executable_passes} passes occur in gates categorized as execution-required by the historical runner; {independently_reproduced_executable_passes} state independent reproduction. This does not establish whether a single-operator execution artifact existed."),
        _check("reproducibility-pass-consistency", "A reproducibility PASS agrees with the card reproduction level", "PASS" if reproducibility_passes == 0 else "FAIL", 0, reproducibility_passes, f"{reproducibility_passes} reproducibility-gate checks are marked passed while their cards state not independently reproduced."),
        _check("report-status", "Manual-review rows exactly cover cards and agree on status", "PASS" if set(reviews) == set(candidates) and report_status_mismatches == 0 else "FAIL", len(set(reviews) & set(candidates))-report_status_mismatches, 7000, f"Unique review records: {len(reviews)}; missing={len(set(candidates)-set(reviews))}, extra={len(set(reviews)-set(candidates))}, status mismatches={report_status_mismatches}."),
        _check("report-http", "Manual-review HTTP metadata agrees with the comparable card observation", "PASS" if report_http_comparable == 7000 and report_http_mismatches == 0 else "FAIL", report_http_comparable-report_http_mismatches, 7000, f"Comparable: {report_http_comparable}; mismatches: {report_http_mismatches}."),
        _check("report-sha", "Manual-review source hash agrees with the comparable card observation", "PASS" if report_sha_comparable == 7000 and report_sha_mismatches == 0 else "FAIL", report_sha_comparable-report_sha_mismatches, 7000, f"Comparable: {report_sha_comparable}; mismatches: {report_sha_mismatches}."),
        _check("report-file-integrity", "Published manual-review files match the hashes recorded by cards", "PASS" if report_file_hash_matches == 7000 else "FAIL", report_file_hash_matches, 7000, f"Checked {len(report_hash_cache)} distinct manual-review files against each card's sanitized_report_sha256."),
        _check("source-manifest-publication", "Every execution batch publishes its referenced source manifest", "PASS" if source_manifest_hash_matches == 34 else "FAIL", source_manifest_hash_matches, 34, f"Published {source_manifest_present}/34 source manifests; all {source_manifest_hash_matches} present referenced manifests match their declared hashes. {34-source_manifest_present} are absent, and {34-source_manifest_declared} execution manifest does not declare a source-manifest hash."),
        _check("independent-reproduction", "Outcome was independently reproduced", "LIMITATION", sum(card.get("reproduction_level") != "not independently reproduced" for _, card in cards.values()), 7000, "All 7,000 cards state not independently reproduced; verification_level is SINGLE_OPERATOR on 6,790 cards and SINGLE_OPERATOR_RERUN on 210."),
        _check("selection-timing", "Source was frozen before first fetch", "PASS" if selection_provenance == 7000 else "NOT_AUDITABLE", selection_provenance if selection_provenance == 7000 else None, 7000, "End-state artifacts assert this rule and URLs match, but current timestamped discovery provenance is incomplete, so ordering is not independently established."),
        _check("no-source-replacement", "Blocked or weak source was not replaced after observation", "PASS" if selection_provenance == 7000 and manifest_url_matches == 7000 else "NOT_AUDITABLE", manifest_url_matches if selection_provenance == 7000 else None, 7000, "Manifest/card URLs match and review text asserts no replacement; without complete pre-evaluation selection provenance, post-observation replacement cannot be independently excluded."),
    ]
    validator_runs: list[dict[str, Any]] = []
    if run_validator:
        for issue in range(166, 200):
            path = ROOT / "artifacts" / f"claim_batch_{issue}_execution_manifest.json"
            process = subprocess.run(
                ["python3", str(ROOT / "scripts/build_public_claim_catalog.py"), "validate-execution-manifest", str(path)],
                capture_output=True,
                text=True,
            )
            lines = (process.stderr or process.stdout).splitlines()
            error_lines = [line for line in lines if line.startswith("ERROR:")]
            validator_runs.append({"issue": issue, "passed": process.returncode == 0, "returncode": process.returncode, "error_count": len(error_lines), "first_error": error_lines[:1]})

    minimum_validator_errors = (
        (7000 - source_roles)
        + (7000 - selection_provenance)
        + 2 * (100 - domain_url_passes)
    )
    observed_validator_errors = (
        sum(item["error_count"] for item in validator_runs) if validator_runs else None
    )
    passing_batches = (
        sum(item["passed"] for item in validator_runs) if validator_runs else None
    )
    failing_batches = (
        len(validator_runs) - passing_batches if validator_runs else None
    )
    structured_reason_codes = sum(
        bool(review.get("reason_code"))
        or bool(REASON_RE.search(cards[claim_id][1].get("manual_review", "")))
        for claim_id, review in reviews.items()
        if claim_id in cards
    )
    legacy_text_classifications = sum(
        card.get("result_status") == "INSUFFICIENT_COVERAGE"
        and not reviews.get(claim_id, {}).get("reason_code")
        and REASON_RE.search(card.get("manual_review", "")) is None
        for claim_id, (_, card) in cards.items()
    )
    conclusion = (
        "CURRENT_PROTOCOL_COMPLIANCE_ESTABLISHED"
        if not any(item["status"] in {"FAIL", "NOT_AUDITABLE"} for item in checks)
        else "COMPLETE_CARD_SET_BUT_CURRENT_PROTOCOL_COMPLIANCE_NOT_ESTABLISHED"
    )

    return {
        "audit_version": "2026-07-26-v1",
        "scope": {"campaign_issue": 165, "batch_issues": "166-199", "claims": 7000, "domains": 100, "topic_source_groups": len(topic_groups)},
        "conclusion": conclusion,
        "outcome_counts": outcome_counts,
        "outcome_percentages": {key: round(value / 7000 * 100, 2) for key, value in outcome_counts.items()},
        "reason_counts": dict(cause_counts),
        "http_status_counts": {"card_raw_manifest_observation": dict(http_status_counts), "manual_review_observation": dict(review_http_status_counts)},
        "reason_methodology": {"blocked_http": "Derived from the evidence-card raw_payload_manifest observation; manual-review HTTP can differ, and unpublished attempt history does not establish their sequence.", "structured_or_embedded_reason_codes": structured_reason_codes, "legacy_text_classifications": legacy_text_classifications},
        "topic_source_analysis": {"topic_source_groups": len(topic_groups), "fully_blocked_groups": len(fully_blocked_groups), "fully_blocked_unique_url_strings": blocked_unique_urls, "fully_drifted_groups": sum(all(card["result_status"] == "SOURCE_DRIFT" for card in group) for group in topic_groups.values()), "accessible_adjudicated_groups": sum(not all(card["result_status"] in {"BLOCKED_SOURCE", "SOURCE_DRIFT"} for card in group) for group in topic_groups.values()), "cross_topic_collision_slots": cross_topic_reuse_slots, "cross_topic_repeated_slots_beyond_first": cross_topic_repeated_slots, "high_reuse_sources": high_reuse_sources},
        "gate_result_counts": {gate: dict(counts) for gate, counts in sorted(by_gate.items())},
        "cohort_result_counts": cohort_counts,
        "domain_audit": by_domain,
        "protocol_checks": checks,
        "report_consistency": {"review_records": len(reviews), "status_mismatches": report_status_mismatches, "http_comparable": report_http_comparable, "http_mismatches": report_http_mismatches, "blocked_http_mismatches": blocked_report_http_mismatches, "sha256_comparable": report_sha_comparable, "sha256_mismatches": report_sha_mismatches, "source_url_comparable": report_url_comparable, "source_url_mismatches": report_url_mismatches, "canonical_url_comparable": report_canonical_comparable, "canonical_url_mismatches": report_canonical_mismatches, "report_file_hash_matches": report_file_hash_matches, "distinct_report_files": len(report_hash_cache)},
        "artifact_publication": {"execution_manifests": 34, "manual_review_files": len(report_hash_cache), "source_manifest_hashes_declared": source_manifest_declared, "source_manifests_published": source_manifest_present, "published_source_manifest_hash_matches": source_manifest_hash_matches},
        "current_manifest_summary": {"validator_executed": bool(validator_runs), "passing_batches": passing_batches, "failing_batches": failing_batches, "minimum_campaign_validator_errors": minimum_validator_errors, "observed_total_validator_errors": observed_validator_errors},
        "operator_context": {"automated_ai_assisted": sum(card.get("execution_mode") == "AUTOMATED_AI_ASSISTED" for _, card in cards.values()), "single_operator": sum(card.get("verification_level") == "SINGLE_OPERATOR" for _, card in cards.values()), "single_operator_rerun": sum(card.get("verification_level") == "SINGLE_OPERATOR_RERUN" for _, card in cards.values()), "independently_reproduced": sum(card.get("reproduction_level") != "not independently reproduced" for _, card in cards.values()), "exact_access_timestamps_published": exact_access_timestamps, "redirect_chains_published": recorded_redirect_chains, "source_integrity_passes": source_integrity_passes, "source_manifests_published": published_source_manifests},
        "manifest_validator_runs": validator_runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-validator", action="store_true")
    args = parser.parse_args()
    report = audit_campaign(run_validator=args.run_validator)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
