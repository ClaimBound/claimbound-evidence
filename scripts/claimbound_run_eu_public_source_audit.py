#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Audit official EU public data portal and reuse-guidance pages without storing raw HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes


@dataclass(frozen=True)
class SourceAuditProfile:
    protocol_id: str
    official_source_name: str
    source_url: str
    expected_title_marker: str
    required_links: dict[str, str]
    claim_boundary: str
    known_limitations: tuple[str, ...]
    default_report: Path


PROFILES: dict[str, SourceAuditProfile] = {
    "EU_ODP_SOURCE_AUDIT_D001": SourceAuditProfile(
        protocol_id="EU_ODP_SOURCE_AUDIT_D001",
        official_source_name="European Data Portal (data.europa.eu)",
        source_url="https://data.europa.eu/en",
        expected_title_marker="European Data Portal",
        required_links={
            "datasets_catalog": "https://data.europa.eu/data/datasets?locale=en",
            "hub_search_api": "https://data.europa.eu/api/hub/search/",
            "copyright_notice": "https://dataeuropa.gitlab.io/data-provider-manual/legal-notice/copyright/",
        },
        claim_boundary=(
            "This source-audit record verifies that the European Data Portal landing page "
            "is reachable, serves HTML, and exposes expected dataset catalog, search API and "
            "copyright notice links. It does not download datasets or make a legal conclusion."
        ),
        known_limitations=[
            "No dataset payload was downloaded or committed.",
            "No catalogue coverage or metadata quality claim is made.",
            "Rights evidence is limited to link presence on the landing page.",
        ],
        default_report=Path("artifacts/eu_odp_source_audit_d001_summary.json"),
    ),
    "EEA_LEGAL_REUSE_SOURCE_AUDIT_D001": SourceAuditProfile(
        protocol_id="EEA_LEGAL_REUSE_SOURCE_AUDIT_D001",
        official_source_name="EEA content reuse FAQ",
        source_url=(
            "https://www.eea.europa.eu/en/about/contact-us/faqs/"
            "can-i-use-eea-content-in-my-work-or-in-my-organisations-products"
        ),
        expected_title_marker="Can I use EEA content",
        required_links={
            "legal_notice": "/en/legal-notice",
            "faqs_index": "/en/about/contact-us/faqs",
        },
        claim_boundary=(
            "This source-audit record verifies that the EEA FAQ page on reusing EEA content "
            "is reachable, serves HTML, and exposes expected legal-notice and FAQ navigation "
            "links. It does not make a legal conclusion about reuse rights."
        ),
        known_limitations=[
            "No legal interpretation of EEA reuse terms is made.",
            "Evidence is limited to page reachability and extracted link presence.",
            "FAQ text is not committed; only URL, status, title marker and SHA-256 are recorded.",
        ],
        default_report=Path("artifacts/eea_legal_reuse_source_audit_d001_summary.json"),
    ),
    "EUROSTAT_SOURCE_AUDIT_D001": SourceAuditProfile(
        protocol_id="EUROSTAT_SOURCE_AUDIT_D001",
        official_source_name="Eurostat API detailed guidelines",
        source_url=(
            "https://ec.europa.eu/eurostat/web/user-guides/data-browser/"
            "api-data-access/api-detailed-guidelines"
        ),
        expected_title_marker="API - Detailed guidelines",
        required_links={
            "copyright_notice": "/eurostat/help/copyright-notice",
            "catalogue_api_dcat": (
                "/eurostat/web/user-guides/data-browser/api-data-access/"
                "api-detailed-guidelines/catalogue-api/dcat"
            ),
            "catalogue_api_metabase": (
                "/eurostat/web/user-guides/data-browser/api-data-access/"
                "api-detailed-guidelines/catalogue-api/metabase"
            ),
        },
        claim_boundary=(
            "This source-audit record verifies that the Eurostat API detailed guidelines page "
            "is reachable, serves HTML, and exposes expected copyright and catalogue API "
            "documentation links. It does not call the API or verify statistical data."
        ),
        known_limitations=[
            "No Eurostat API request was executed.",
            "No statistical coverage or data freshness claim is made.",
            "Rights evidence is limited to copyright notice link presence on the page.",
        ],
        default_report=Path("artifacts/eurostat_source_audit_d001_summary.json"),
    ),
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        required=True,
        help="Frozen source-audit profile identifier.",
    )
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--access-date",
        default=None,
        help="ISO access date recorded in the sanitized report. Defaults to today.",
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


def _extract_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(html.unescape(match.group(1)).split())


def _extract_links(text: str) -> set[str]:
    hrefs = re.findall(r"""href=["']([^"']+)["']""", text, flags=re.IGNORECASE)
    srcs = re.findall(r"""src=["']([^"']+)["']""", text, flags=re.IGNORECASE)
    return {html.unescape(value).split("#", 1)[0] for value in hrefs + srcs}


def _link_present(links: set[str], target: str) -> bool:
    normalized = target.rstrip("/")
    return target in links or normalized in links


def build_report(
    profile: SourceAuditProfile,
    fetch: FetchResult,
    access_date: str | None = None,
) -> dict[str, object]:
    text = fetch.body.decode("utf-8", errors="replace")
    title = _extract_title(text)
    links = _extract_links(text)
    required_link_presence = {
        name: _link_present(links, target) for name, target in profile.required_links.items()
    }
    title_marker_present = profile.expected_title_marker.lower() in title.lower()
    html_content = "text/html" in fetch.content_type.lower()

    missing_gate_elements: list[str] = []
    if fetch.status_code != 200:
        missing_gate_elements.append(f"http_status:{fetch.status_code}")
    if not html_content:
        missing_gate_elements.append(f"content_type_not_html:{fetch.content_type}")
    if not title_marker_present:
        missing_gate_elements.append(f"title_marker:{profile.expected_title_marker}")
    for name, present in required_link_presence.items():
        if not present:
            missing_gate_elements.append(f"required_link:{name}")

    pass_gate = (
        fetch.status_code == 200
        and html_content
        and title_marker_present
        and all(required_link_presence.values())
    )

    return {
        "access_date": access_date or date.today().isoformat(),
        "protocol_id": profile.protocol_id,
        "record_type": "source_audit",
        "pass_gate": pass_gate,
        "result_status": "PASSED_UNDER_PROTOCOL" if pass_gate else "BLOCKED_SOURCE",
        "card_validity_level": "GREEN_VALIDATED" if pass_gate else "RED_INVALID_OR_TAMPER_EVIDENCE",
        "official_source_name": profile.official_source_name,
        "official_source_url": profile.source_url,
        "final_url": fetch.url,
        "http_status": fetch.status_code,
        "content_type": fetch.content_type,
        "page_title": title,
        "page_sha256": hashlib.sha256(fetch.body).hexdigest(),
        "page_byte_size": len(fetch.body),
        "expected_title_marker": profile.expected_title_marker,
        "title_marker_present": title_marker_present,
        "required_link_presence": required_link_presence,
        "required_links": profile.required_links,
        "missing_gate_elements": missing_gate_elements,
        "raw_payload_committed": False,
        "raw_payload_policy": (
            "Raw HTML is not committed; only source URL, status, extracted link presence, "
            "title marker presence, byte size and SHA-256 are recorded."
        ),
        "claim_boundary": profile.claim_boundary,
        "known_limitations": list(profile.known_limitations),
    }


def main() -> int:
    args = _build_parser().parse_args()
    profile = PROFILES[args.profile]
    report_path = args.report or profile.default_report
    report = build_report(profile, fetch_source(profile.source_url), args.access_date)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
