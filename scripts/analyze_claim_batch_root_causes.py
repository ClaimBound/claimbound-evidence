#!/usr/bin/env python3
"""Explain BLOCKED_SOURCE and INSUFFICIENT_COVERAGE in frozen claim batches."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from claimbound_gate_locator import locate_gate


def parse_issue_range(value: str) -> range:
    start, separator, end = value.partition(":")
    if not separator:
        issue = int(start)
        return range(issue, issue + 1)
    return range(int(start), int(end) + 1)


def text_length_class(text: str) -> str:
    length = len(text.strip())
    if length < 100:
        return "under_100_chars"
    if length < 500:
        return "100_to_499_chars"
    if length < 2_000:
        return "500_to_1999_chars"
    return "at_least_2000_chars"


def insufficient_cause(text: str) -> str:
    length_class = text_length_class(text)
    if length_class in {"under_100_chars", "100_to_499_chars"}:
        return "VERY_SHORT_OR_SHELL_EXTRACTION"
    if length_class == "500_to_1999_chars":
        return "SHORT_EXTRACT_REQUIRES_REVIEW"
    return "GATE_SPECIFIC_FACETS_MISSING"


def blocked_cause(http_status: int) -> str:
    if http_status == 404:
        return "STALE_OR_INCORRECT_EXACT_URL"
    if http_status in {401, 403, 429, 444}:
        return "ACCESS_POLICY_OR_ANTI_BOT"
    if http_status == 0:
        return "TRANSPORT_FAILURE"
    return "OTHER_HTTP_FAILURE"


def source_key(row: dict[str, Any]) -> str:
    return f"{row['domain_code']}-T{int(row['topic_index']):02d}"


def sorted_counter(counter: Counter[Any]) -> dict[str, int]:
    return {
        str(key): value
        for key, value in sorted(counter.items(), key=lambda item: str(item[0]))
    }


def analyze(
    report_paths: Iterable[Path],
    cache_template: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for report_path in report_paths:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        issue = int(report["issue_number"])
        rows.extend({**row, "_issue": issue} for row in report["cards"])

    status_counts = Counter(row["status"] for row in rows)
    blocked_rows = [row for row in rows if row["status"] == "BLOCKED_SOURCE"]
    insufficient_rows = [row for row in rows if row["status"] == "INSUFFICIENT_COVERAGE"]

    blocked_sources = {
        (row["_issue"], source_key(row)): row
        for row in blocked_rows
    }
    blocked_hosts = Counter(
        (urlparse(row["source_url"]).hostname or "").removeprefix("www.")
        for row in blocked_sources.values()
    )

    text_classes: Counter[str] = Counter()
    insufficient_causes: Counter[str] = Counter()
    recorded_reason_codes = Counter(
        row.get("reason_code", "LEGACY_REASON_UNRECORDED")
        for row in insufficient_rows
    )
    insufficient_gates = Counter(row["gate"] for row in insufficient_rows)
    missing_facets: Counter[str] = Counter()
    cache_files_missing = 0
    source_cache: dict[tuple[int, str], str] = {}
    for row in insufficient_rows:
        key = (row["_issue"], source_key(row))
        if key not in source_cache:
            cache_root = Path(cache_template.format(issue=row["_issue"]))
            text_path = cache_root / "text" / f"{key[1]}.txt"
            if text_path.exists():
                source_cache[key] = text_path.read_text(encoding="utf-8", errors="replace")
            else:
                source_cache[key] = ""
                cache_files_missing += 1
        text = source_cache[key]
        text_classes[text_length_class(text)] += 1
        insufficient_causes[insufficient_cause(text)] += 1
        decision = locate_gate(text, str(row["topic"]), str(row["gate"]))
        for facet in decision.missing_facets:
            missing_facets[f"{row['gate']}:{facet}"] += 1

    recovered_sources = []
    all_source_keys = {
        (row["_issue"], source_key(row))
        for row in rows
    }
    for issue, key in sorted(all_source_keys):
        meta_path = Path(cache_template.format(issue=issue)) / "meta" / f"{key}.json"
        if not meta_path.exists():
            continue
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        attempts = metadata.get("attempts", [])
        if (
            metadata.get("http_status") == 200
            and any(attempt.get("http_status") in {0, 403, 429, 444} for attempt in attempts[:-1])
        ):
            recovered_sources.append(
                {
                    "issue": issue,
                    "source_key": key,
                    "selected_transport_profile": metadata.get("selected_transport_profile"),
                }
            )

    blocked_http_cards = Counter(row["http_status"] for row in blocked_rows)
    blocked_http_sources = Counter(row["http_status"] for row in blocked_sources.values())
    blocked_cause_cards = Counter(blocked_cause(int(row["http_status"])) for row in blocked_rows)
    blocked_cause_sources = Counter(
        blocked_cause(int(row["http_status"])) for row in blocked_sources.values()
    )
    pass_by_gate = Counter(
        row["gate"] for row in rows if row["status"] == "PASSED_UNDER_PROTOCOL"
    )
    return {
        "claim_boundary": (
            "Root-cause audit of already frozen batch reports and local response caches; "
            "this analysis does not replace sources or reclassify outcomes by target quota."
        ),
        "raw_payload_committed": False,
        "scope": {
            "issues": sorted({row["_issue"] for row in rows}),
            "cards": len(rows),
            "unique_topic_sources": len(all_source_keys),
        },
        "status_counts": sorted_counter(status_counts),
        "blocked_source": {
            "cards": len(blocked_rows),
            "unique_sources": len(blocked_sources),
            "by_http_status_cards": sorted_counter(blocked_http_cards),
            "by_http_status_sources": sorted_counter(blocked_http_sources),
            "by_cause_cards": sorted_counter(blocked_cause_cards),
            "by_cause_sources": sorted_counter(blocked_cause_sources),
            "top_hosts": [
                {"host": host, "sources": count, "cards": count * 10}
                for host, count in blocked_hosts.most_common(20)
            ],
            "same_url_transport_recoveries": recovered_sources,
        },
        "insufficient_coverage": {
            "cards": len(insufficient_rows),
            "by_gate": sorted_counter(insufficient_gates),
            "by_extracted_text_length": sorted_counter(text_classes),
            "by_cause": sorted_counter(insufficient_causes),
            "by_recorded_reason_code": sorted_counter(recorded_reason_codes),
            "missing_gate_facets": sorted_counter(missing_facets),
            "missing_cache_files": cache_files_missing,
        },
        "passed_by_gate": sorted_counter(pass_by_gate),
        "interpretation": [
            "One topic source is reused by ten gate cards, so one inaccessible URL produces ten BLOCKED_SOURCE cards.",
            "A long extraction can still be INSUFFICIENT_COVERAGE when it lacks one or more preregistered gate facets.",
            "A transport or extraction failure must not be converted into a pass by substituting a source after evaluation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issues", default="172:184")
    parser.add_argument(
        "--report-template",
        default="artifacts/claim_batch_{issue}_manual_review.json",
    )
    parser.add_argument(
        "--cache-template",
        default="/private/tmp/claim_batch_{issue}",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    issues = parse_issue_range(args.issues)
    report_paths = [Path(args.report_template.format(issue=issue)) for issue in issues]
    result = analyze(report_paths, args.cache_template)
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
