# SPDX-License-Identifier: Apache-2.0
"""Shared test data for the core tests."""

from __future__ import annotations

import copy
from typing import Any

from protocolith.core import sha256_hex

HASH_A = "a" * 64
HASH_B = "b" * 64
NOW = "2026-11-15T10:00:00Z"
PROTOCOL: dict[str, Any] = {"gate": "pass rate at least 0.5", "protocol_id": "DEMO_D001", "version": "1"}
PROTOCOL_SHA = sha256_hex(PROTOCOL)
CARD: dict[str, Any] = {
    "operator": "local operator",
    "official_source_name": "Demo source",
    "official_source_url": "https://example.org/data",
    "domain": "demo",
    "claim_type": "source_audit",
    "access_date": "2026-11-15",
    "source_rights_note": "Public page, no raw payload stored.",
    "raw_payload_manifest": "No raw payload committed.",
    "sanitized_report_path": "artifacts/demo_report.json",
    "sanitized_report_sha256": HASH_A,
    "git_commit": "abc1234",
    "runner_command": "manual",
    "verification_count": 1,
    "verification_level": "SINGLE_OPERATOR",
    "execution_mode": "MANUAL_NO_AI",
    "ai_assistance": "not used",
    "manual_review": "Reviewed by the operator.",
    "known_limitations": ["Single operator."],
    "baseline_control_summary": "Baseline: previous value.",
    "public_claim_text": "The demo source publishes a statement about demo data.",
    "public_claim_verbatim_quote": "A verbatim quote of the demo statement.",
    "public_claim_source_url": "https://example.org/data",
    "public_claim_locator": "section 1, paragraph 2",
    "public_claim_captured_at": "2026-11-15",
    "public_claim_source_sha256": HASH_B,
}


def protocol() -> dict[str, Any]:
    return copy.deepcopy(PROTOCOL)


def record_body(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "protocol_sha256": PROTOCOL_SHA,
        "run_id": "run-1",
        "status": "PASSED_UNDER_PROTOCOL",
        "outcome": {"pass_rate": "0.55"},
        "sources": [{"id": "source-1", "sha256": HASH_A}],
        "reproduction_level": "not independently reproduced",
        "claim_boundary": "Only the stated gate on the stated source and period.",
        "deviations": [],
        "card": copy.deepcopy(CARD),
    }
    body.update(changes)
    return {key: value for key, value in body.items() if value is not None}


def deviation_body() -> dict[str, Any]:
    return {"protocol_sha256": PROTOCOL_SHA, "kind": "source_change", "description": "The source moved."}


def clock(value: str = NOW) -> Any:
    return lambda: value
