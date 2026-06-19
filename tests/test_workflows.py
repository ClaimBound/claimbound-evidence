# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from claimbound_evidence.workflows import drift_eea_source_audit


def test_drift_eea_source_audit_reports_changed_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from claimbound_evidence import cli

    repo = tmp_path / "repo"
    repo.mkdir()
    baseline = {
        "http_status": 200,
        "final_url": "https://example.org/",
        "content_type": "text/html",
        "page_sha256": "aaa",
        "page_byte_size": 10,
        "page_title": "t",
        "rights_link_present": True,
        "direct_link_presence": {"current_download_service": True},
        "result_status": "PASSED_UNDER_PROTOCOL",
    }
    fresh = dict(baseline)
    fresh["page_sha256"] = "bbb"
    baseline_path = repo / "artifacts" / "source_audit_d001_summary.json"
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    report_path = repo / "artifacts" / "eea_source_audit_drift_check_summary.json"
    report_path.write_text(json.dumps(fresh), encoding="utf-8")

    monkeypatch.setattr(cli, "REPO_ROOT", repo)

    with patch(
        "claimbound_evidence.workflows.subprocess.call",
        return_value=0,
    ):
        assert (
            drift_eea_source_audit(
                repo,
                baseline_path=baseline_path,
                report_path=report_path,
            )
            == 0
        )

    out = capsys.readouterr().out
    assert "changed_fields=page_sha256" in out