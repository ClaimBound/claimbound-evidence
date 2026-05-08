#!/usr/bin/env python3
"""Audit the EEA Air Quality download source boundary without storing raw HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path


SOURCE_URL = "https://aqportal.discomap.eea.europa.eu/download-data/"
EXPECTED_TITLE = "Download data"
EXPECTED_DIRECT_LINKS = {
    "current_download_service": "https://eeadmz1-downloads-webapp.azurewebsites.net/",
    "airbase_legacy": "https://discomap.eea.europa.eu/map/fme/AirQualityExportAirBase.htm",
    "e1a_legacy": "https://discomap.eea.europa.eu/map/fme/AirQualityExport.htm",
    "e2a_legacy": "https://discomap.eea.europa.eu/map/fme/AirQualityUTDExport.htm",
    "zone_geometries": "https://discomap.eea.europa.eu/map/FME/AQZones/",
    "discodata": "https://discodata.eea.europa.eu/",
}
RIGHTS_LINK = "https://www.eea.europa.eu/legal/copyright"


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--report", required=True, type=Path)
    return parser


def fetch_source(url: str) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": "ClaimBound-source-audit/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return FetchResult(
            url=response.geturl(),
            status_code=response.status,
            content_type=response.headers.get("content-type", ""),
            body=response.read(),
        )


def build_report(fetch: FetchResult) -> dict[str, object]:
    text = fetch.body.decode("utf-8", errors="replace")
    title = _extract_title(text)
    links = _extract_links(text)
    direct_link_presence = {
        name: target in links or target.rstrip("/") in links
        for name, target in EXPECTED_DIRECT_LINKS.items()
    }

    pass_gate = (
        fetch.status_code == 200
        and "text/html" in fetch.content_type.lower()
        and EXPECTED_TITLE.lower() in title.lower()
        and direct_link_presence["current_download_service"]
        and RIGHTS_LINK in links
    )

    return {
        "protocol_id": "SOURCE_AUDIT_D001",
        "record_type": "source_audit",
        "result_status": "PASSED_UNDER_PROTOCOL" if pass_gate else "BLOCKED_SOURCE",
        "card_validity_level": "GREEN_VALIDATED" if pass_gate else "RED_INVALID_OR_TAMPER_EVIDENCE",
        "official_source_name": "EEA Air Quality Download Service",
        "official_source_url": SOURCE_URL,
        "final_url": fetch.url,
        "http_status": fetch.status_code,
        "content_type": fetch.content_type,
        "page_title": title,
        "page_sha256": hashlib.sha256(fetch.body).hexdigest(),
        "page_byte_size": len(fetch.body),
        "direct_link_presence": direct_link_presence,
        "rights_link_present": RIGHTS_LINK in links,
        "rights_link": RIGHTS_LINK,
        "raw_payload_committed": False,
        "raw_payload_policy": "Raw HTML and downloadable datasets are not committed; only source URL, status, extracted link presence and SHA-256 are recorded.",
        "claim_boundary": (
            "This source-audit record verifies that the EEA Air Quality Portal download page "
            "is reachable and exposes expected download-service and rights links. It does not "
            "download datasets, verify dataset coverage, or make a legal conclusion."
        ),
        "known_limitations": [
            "No air-quality dataset payload was downloaded or committed.",
            "No pollutant, station or time coverage claim is made.",
            "Rights evidence is limited to finding the EEA copyright notice link; no legal conclusion is made.",
        ],
    }


def _extract_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(html.unescape(match.group(1)).split())


def _extract_links(text: str) -> set[str]:
    hrefs = re.findall(r"""href=["']([^"']+)["']""", text, flags=re.IGNORECASE)
    srcs = re.findall(r"""src=["']([^"']+)["']""", text, flags=re.IGNORECASE)
    return {html.unescape(value).split("#", 1)[0] for value in hrefs + srcs}


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report(fetch_source(args.source_url))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.report.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
