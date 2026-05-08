from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "claimbound_run_public_doc_source_audit.py"
SPEC = importlib.util.spec_from_file_location("claimbound_run_public_doc_source_audit", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

FetchResult = MODULE.FetchResult
build_report = MODULE.build_report


def test_public_doc_source_audit_passes_on_expected_markers() -> None:
    report = build_report(
        fetch=FetchResult(
            url="https://example.org/card",
            status_code=200,
            content_type="text/html; charset=utf-8",
            body=b"<html><title>System Card</title><h1>Provider System Card</h1></html>",
        ),
        protocol_id="EXAMPLE_SOURCE_AUDIT_D001",
        source_name="Example system card",
        source_url="https://example.org/card",
        expected_tokens=["System Card", "Provider"],
        claim_boundary="Source audit only.",
    )

    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["raw_payload_committed"] is False


def test_public_doc_source_audit_blocks_missing_markers() -> None:
    report = build_report(
        fetch=FetchResult(
            url="https://example.org/card",
            status_code=200,
            content_type="text/html",
            body=b"<html><title>Other Page</title></html>",
        ),
        protocol_id="EXAMPLE_SOURCE_AUDIT_D001",
        source_name="Example system card",
        source_url="https://example.org/card",
        expected_tokens=["System Card"],
        claim_boundary="Source audit only.",
    )

    assert report["result_status"] == "BLOCKED_SOURCE"
