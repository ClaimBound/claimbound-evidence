# SPDX-License-Identifier: Apache-2.0
"""Tests for the EU public source-audit runner (mocked HTTP)."""

from __future__ import annotations

import importlib.util as ilu
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "claimbound_run_eu_public_source_audit.py"
BUILDER_PATH = REPO_ROOT / "scripts" / "claimbound_build_eu_evidence_cards.py"


def _load_runner():
    spec = ilu.spec_from_file_location("claimbound_run_eu_public_source_audit_mod", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_builder():
    spec = ilu.spec_from_file_location("claimbound_build_eu_evidence_cards_mod", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


def test_eu_odp_report_passes_for_expected_landing_page(runner) -> None:
    body = b"""
    <html>
      <head><title>The European Data Portal</title></head>
      <body>
        <a href="https://data.europa.eu/data/datasets?locale=en">datasets</a>
        <a href="https://data.europa.eu/api/hub/search/">api</a>
        <a href="https://dataeuropa.gitlab.io/data-provider-manual/legal-notice/copyright/">copyright</a>
      </body>
    </html>
    """
    fetch = runner.FetchResult(
        url=runner.PROFILES["EU_ODP_SOURCE_AUDIT_D001"].source_url,
        status_code=200,
        content_type="text/html; charset=UTF-8",
        body=body,
    )

    report = runner.build_report(runner.PROFILES["EU_ODP_SOURCE_AUDIT_D001"], fetch)

    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["access_date"]
    assert report["raw_payload_committed"] is False
    assert report["required_link_presence"]["datasets_catalog"] is True


def test_eea_legal_reuse_report_passes_for_expected_faq_page(runner) -> None:
    body = b"""
    <html>
      <head><title>Can I use EEA content in my work?</title></head>
      <body>
        <a href="/en/legal-notice">legal</a>
        <a href="/en/about/contact-us/faqs">faqs</a>
      </body>
    </html>
    """
    fetch = runner.FetchResult(
        url=runner.PROFILES["EEA_LEGAL_REUSE_SOURCE_AUDIT_D001"].source_url,
        status_code=200,
        content_type="text/html; charset=utf-8",
        body=body,
    )

    report = runner.build_report(runner.PROFILES["EEA_LEGAL_REUSE_SOURCE_AUDIT_D001"], fetch)

    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["title_marker_present"] is True


def test_eurostat_report_passes_for_expected_guidelines_page(runner) -> None:
    body = b"""
    <html>
      <head><title>API - Detailed guidelines - User guides - Eurostat</title></head>
      <body>
        <a href="/eurostat/help/copyright-notice">copyright</a>
        <a href="/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/catalogue-api/dcat">dcat</a>
        <a href="/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/catalogue-api/metabase">meta</a>
      </body>
    </html>
    """
    fetch = runner.FetchResult(
        url=runner.PROFILES["EUROSTAT_SOURCE_AUDIT_D001"].source_url,
        status_code=200,
        content_type="text/html;charset=UTF-8",
        body=body,
    )

    report = runner.build_report(runner.PROFILES["EUROSTAT_SOURCE_AUDIT_D001"], fetch)

    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["required_link_presence"]["catalogue_api_dcat"] is True


def test_eu_odp_report_blocks_when_copyright_link_missing(runner) -> None:
    fetch = runner.FetchResult(
        url=runner.PROFILES["EU_ODP_SOURCE_AUDIT_D001"].source_url,
        status_code=200,
        content_type="text/html",
        body=b"<title>European Data Portal</title>",
    )

    report = runner.build_report(runner.PROFILES["EU_ODP_SOURCE_AUDIT_D001"], fetch)

    assert report["result_status"] == "BLOCKED_SOURCE"
    assert "required_link:copyright_notice" in report["missing_gate_elements"]


def test_main_writes_report_with_mocked_fetch(runner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = runner.PROFILES["EU_ODP_SOURCE_AUDIT_D001"]
    report_path = tmp_path / "eu_odp_summary.json"
    fetch = runner.FetchResult(
        url=profile.source_url,
        status_code=200,
        content_type="text/html",
        body=(
            b"<title>European Data Portal</title>"
            b"<a href='https://data.europa.eu/data/datasets?locale=en'>d</a>"
            b"<a href='https://data.europa.eu/api/hub/search/'>a</a>"
            b"<a href='https://dataeuropa.gitlab.io/data-provider-manual/legal-notice/copyright/'>c</a>"
        ),
    )
    monkeypatch.setattr(runner, "fetch_source", lambda _url: fetch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "claimbound_run_eu_public_source_audit.py",
            "--profile",
            "EU_ODP_SOURCE_AUDIT_D001",
            "--report",
            str(report_path),
            "--access-date",
            "2026-06-10",
        ],
    )

    assert runner.main() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["access_date"] == "2026-06-10"
    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["protocol_id"] == "EU_ODP_SOURCE_AUDIT_D001"


def test_card_builder_uses_summary_access_date() -> None:
    builder = _load_builder()
    spec = builder.SPECS[0]
    report = json.loads(spec.artifact.read_text(encoding="utf-8"))

    access_date = builder._report_access_date(report, fallback=None)
    card = builder._build_card(spec, report, "abc123", access_date)

    assert access_date == "2026-06-10"
    assert card["evidence_id"] == "CLAIMBOUND-EU_ODP_SOURCE_AUDIT_D001-2026-06-10"
    assert card["access_date"] == "2026-06-10"


def test_card_builder_requires_date_for_legacy_summary() -> None:
    builder = _load_builder()

    with pytest.raises(ValueError, match="missing access_date"):
        builder._report_access_date({}, fallback=None)

    assert builder._report_access_date({}, fallback="2026-06-10") == "2026-06-10"
