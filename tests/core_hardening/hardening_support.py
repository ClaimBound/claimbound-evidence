# SPDX-License-Identifier: Apache-2.0
"""Shared data and helpers for the hardening tests (independent of tests/core)."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from protocolith.core import Store, deviation, freeze, issue, record, sha256_hex
from protocolith.core.ledger import ZERO_HASH, make_entry, serialize

HASH_A = "a" * 64
HASH_B = "b" * 64
PROTOCOL: dict[str, Any] = {"gate": "pass rate at least 0.5", "protocol_id": "DEMO_D001", "version": "1"}
PROTOCOL_V2: dict[str, Any] = {"gate": "pass rate at least 0.6", "protocol_id": "DEMO_D001", "version": "2"}
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


def ts(second: int) -> str:
    """A valid timestamp ``second`` seconds after 2026-11-15T10:00:00Z (second < 3600)."""
    return f"2026-11-15T10:{second // 60:02d}:{second % 60:02d}Z"


def clock_at(second: int) -> Any:
    return lambda: ts(second)


def protocol(**changes: Any) -> dict[str, Any]:
    out = copy.deepcopy(PROTOCOL)
    out.update(changes)
    return out


def record_body(protocol_sha: str = PROTOCOL_SHA, **changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "protocol_sha256": protocol_sha,
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


def deviation_body(protocol_sha: str = PROTOCOL_SHA, **changes: Any) -> dict[str, Any]:
    body = {"protocol_sha256": protocol_sha, "kind": "source_change", "description": "The source moved."}
    body.update(changes)
    return body


def oracle_bytes(value: Any) -> bytes:
    """Independent PCJ-1 construction from the standard library (valid for the PCJ-1 domain only)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def oracle_entry_hash(entry: dict[str, Any]) -> str:
    return hashlib.sha256(oracle_bytes({k: v for k, v in entry.items() if k != "hash"})).hexdigest()


def build_sample_ledger(path: Path) -> bytes:
    """freeze, deviation, record, freeze v2 (supersedes), record, issue: a ledger touching every entry type."""
    store = Store(path)
    freeze(store, protocol(), clock=clock_at(0))
    deviation(store, deviation_body(), clock=clock_at(1))
    record(store, record_body(deviations=[1]), clock=clock_at(2))
    freeze(store, PROTOCOL_V2, supersedes=PROTOCOL_SHA, clock=clock_at(3))
    record(store, record_body(sha256_hex(PROTOCOL_V2), run_id="run-2"), clock=clock_at(4))
    issue(store, 4, clock=clock_at(5))
    return store.ledger_path.read_bytes()


def fast_ledger(count: int, *, body_note: str = "x") -> bytes:
    """A valid ledger of ``count`` entries (one freeze, then deviations), built without the ops layer."""
    prev = ZERO_HASH
    parts: list[bytes] = []
    for seq in range(count):
        if seq == 0:
            kind = "freeze"
            body: dict[str, Any] = {
                "protocol_id": "DEMO_D001",
                "protocol": PROTOCOL,
                "protocol_sha256": PROTOCOL_SHA,
                "supersedes": None,
                "version": "1",
            }
        else:
            kind = "deviation"
            body = deviation_body(description=f"{body_note} {seq}")
        entry = make_entry(seq=seq, prev=prev, ts=ts(0), type=kind, body=body)
        parts.append(serialize(entry))
        prev = entry["hash"]
    return b"".join(parts)
