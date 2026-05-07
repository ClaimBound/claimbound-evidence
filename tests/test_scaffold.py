# SPDX-License-Identifier: Apache-2.0
"""Tests for ClaimBound track scaffolding."""

from __future__ import annotations

import json
from pathlib import Path

from claimbound_public_benchmarks.scaffold import ScaffoldRequest, build_scaffold


def test_scaffold_creates_draft_without_result_status(tmp_path: Path) -> None:
    request = ScaffoldRequest(
        source_url="https://example.org/source",
        protocol_id="EXAMPLE_D001",
        domain="example-domain",
        track_type="source_audit",
        execution_mode="MANUAL_NO_AI",
        out_dir=tmp_path / "docs" / "manual_audit" / "EXAMPLE_D001",
        source_name="Example public source",
        audience="Example audience",
    )

    paths = build_scaffold(request, tmp_path)

    rel_paths = {path.relative_to(tmp_path).as_posix() for path in paths}
    assert rel_paths == {
        "docs/protocols/EXAMPLE_D001_PREREG_CHARTER.md",
        "docs/evidence_requests/EXAMPLE_D001_REQUEST.md",
        "docs/manual_audit/EXAMPLE_D001/EXAMPLE_D001_PLAYBOOK.md",
        "docs/manual_audit/EXAMPLE_D001/EXAMPLE_D001_CHECKLIST.md",
        "docs/manual_audit/EXAMPLE_D001/EXAMPLE_D001_OPERATOR_DECLARATION.md",
        "docs/evidence_card_drafts/CLAIMBOUND-EXAMPLE_D001-DRAFT.json",
        "artifacts/example_d001_source_probe_summary.json",
    }

    card = json.loads(
        (tmp_path / "docs/evidence_card_drafts/CLAIMBOUND-EXAMPLE_D001-DRAFT.json").read_text(
            encoding="utf-8"
        )
    )
    assert card["draft_status"] == "GRAY_DRAFT_NOT_EXECUTED"
    assert card["raw_payload_committed"] is False
    assert "result_status" not in card
    assert "PASSED_UNDER_PROTOCOL" not in json.dumps(card)

    probe = json.loads(
        (tmp_path / "artifacts/example_d001_source_probe_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert probe["network_fetch_performed"] is False
    assert probe["claim_boundary"]
