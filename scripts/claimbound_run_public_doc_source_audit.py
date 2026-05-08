#!/usr/bin/env python3
"""Audit an official public documentation page without storing raw page content."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--expect",
        action="append",
        default=[],
        help="Case-insensitive text marker expected in the fetched page.",
    )
    parser.add_argument(
        "--claim-boundary",
        required=True,
        help="Narrow claim boundary recorded in the sanitized report.",
    )
    return parser


def fetch_source(url: str) -> FetchResult:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 ClaimBound-source-audit/0.2",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return FetchResult(
            url=response.geturl(),
            status_code=response.status,
            content_type=response.headers.get("content-type", ""),
            body=response.read(),
        )


def build_report(
    *,
    fetch: FetchResult,
    protocol_id: str,
    source_name: str,
    source_url: str,
    expected_tokens: list[str],
    claim_boundary: str,
) -> dict[str, object]:
    text = fetch.body.decode("utf-8", errors="replace")
    normalized = " ".join(html.unescape(text).split()).lower()
    expected_token_presence = {
        token: token.lower() in normalized for token in expected_tokens
    }
    content_type = fetch.content_type.lower()
    supported_content_type = (
        "text/html" in content_type
        or "text/plain" in content_type
        or "application/pdf" in content_type
    )
    pass_gate = (
        fetch.status_code == 200
        and supported_content_type
        and all(expected_token_presence.values())
    )

    return {
        "protocol_id": protocol_id,
        "record_type": "source_audit",
        "result_status": "PASSED_UNDER_PROTOCOL" if pass_gate else "BLOCKED_SOURCE",
        "card_validity_level": "GREEN_VALIDATED" if pass_gate else "RED_INVALID_OR_TAMPER_EVIDENCE",
        "official_source_name": source_name,
        "official_source_url": source_url,
        "final_url": fetch.url,
        "http_status": fetch.status_code,
        "content_type": fetch.content_type,
        "page_title": _extract_title(text),
        "page_sha256": hashlib.sha256(fetch.body).hexdigest(),
        "page_byte_size": len(fetch.body),
        "expected_token_presence": expected_token_presence,
        "raw_payload_committed": False,
        "raw_payload_policy": "Raw page content is not committed; only URL, status, content type, expected-token presence, byte size and SHA-256 are recorded.",
        "claim_boundary": claim_boundary,
        "known_limitations": [
            "This is a source-boundary audit only.",
            "No model quality, safety, benchmark-performance or deployment-readiness claim is made.",
            "No legal conclusion is made about reuse rights.",
        ],
    }


def _extract_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.IGNORECASE | re.DOTALL)
        if not h1:
            return ""
        return _clean_html_text(h1.group(1))
    return _clean_html_text(match.group(1))


def _clean_html_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report(
        fetch=fetch_source(args.source_url),
        protocol_id=args.protocol_id,
        source_name=args.source_name,
        source_url=args.source_url,
        expected_tokens=args.expect,
        claim_boundary=args.claim_boundary,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.report.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
