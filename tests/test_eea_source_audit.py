# SPDX-License-Identifier: Apache-2.0
"""Tests for the EEA source-audit runner."""

from __future__ import annotations

import importlib.util as ilu
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    script_path = REPO_ROOT / "scripts" / "claimbound_run_eea_source_audit.py"
    spec = ilu.spec_from_file_location("claimbound_run_eea_source_audit_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_eea_report_passes_for_expected_source_page() -> None:
    runner = _load_runner()
    body = b"""
    <html>
      <head><title>Download data - European Air Quality Portal</title></head>
      <body>
        <a href="https://eeadmz1-downloads-webapp.azurewebsites.net/">current</a>
        <a href="https://discomap.eea.europa.eu/map/fme/AirQualityExportAirBase.htm">airbase</a>
        <a href="https://discomap.eea.europa.eu/map/fme/AirQualityExport.htm">e1a</a>
        <a href="https://discomap.eea.europa.eu/map/fme/AirQualityUTDExport.htm">e2a</a>
        <a href="https://discomap.eea.europa.eu/map/FME/AQZones/">zones</a>
        <a href="https://discodata.eea.europa.eu/">discodata</a>
        <a href="https://www.eea.europa.eu/legal/copyright">copyright</a>
      </body>
    </html>
    """
    fetch = runner.FetchResult(
        url=runner.SOURCE_URL,
        status_code=200,
        content_type="text/html; charset=UTF-8",
        body=body,
    )

    report = runner.build_report(fetch)

    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["raw_payload_committed"] is False
    assert report["rights_link_present"] is True
    assert report["direct_link_presence"]["current_download_service"] is True


def test_eea_report_blocks_when_current_download_link_missing() -> None:
    runner = _load_runner()
    fetch = runner.FetchResult(
        url=runner.SOURCE_URL,
        status_code=200,
        content_type="text/html",
        body=b"<title>Download data</title><a href='https://www.eea.europa.eu/legal/copyright'>copyright</a>",
    )

    report = runner.build_report(fetch)

    assert report["result_status"] == "BLOCKED_SOURCE"
