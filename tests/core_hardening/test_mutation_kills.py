# SPDX-License-Identifier: Apache-2.0
"""Tests added for surviving mutants that were not message-text only (see scripts/mutation_core.sh)."""

from __future__ import annotations

from typing import Any

from hardening_support import HASH_A, PROTOCOL, PROTOCOL_SHA, record_body, ts

from protocolith.core import scan
from protocolith.core.ledger import ZERO_HASH, make_entry, serialize


def freeze_entry(**changes: Any) -> dict[str, Any]:
    body = {"protocol_id": "DEMO_D001", "protocol": PROTOCOL, "protocol_sha256": PROTOCOL_SHA, "supersedes": None, "version": "1"}
    body.update(changes)
    return make_entry(seq=0, prev=ZERO_HASH, ts=ts(0), type="freeze", body=body)


def test_non_string_version_is_a_verdict_not_an_exception() -> None:
    for version in (1, None, ["1"], {"a": 1}, True):
        verdict, _ = scan(serialize(freeze_entry(version=version)), None)
        assert verdict.codes == ["BAD_ENTRY"]


def test_every_violation_has_a_message_and_truncated_tail_points_at_the_partial_line() -> None:
    first = freeze_entry()
    second = make_entry(seq=5, prev=HASH_A, ts=ts(1), type="record", body=record_body())
    second["hash"] = HASH_A
    data = serialize(first) + serialize(second).replace(b'"v":1}', b'"v":1 }') + b'{"bo'
    verdict, _ = scan(data, None)
    assert {"BAD_SEQ", "BAD_PREV", "BAD_HASH", "NOT_CANONICAL", "TRUNCATED_TAIL"} <= set(verdict.codes)
    assert all(isinstance(v.message, str) and len(v.message) > 10 for v in verdict.violations)
    tail = [v for v in verdict.violations if v.code == "TRUNCATED_TAIL"]
    assert [v.seq for v in tail] == [2]


def test_duplicate_freeze_message_names_id_and_version() -> None:
    first = freeze_entry()
    again = make_entry(seq=1, prev=first["hash"], ts=ts(1), type="freeze", body=first["body"])
    verdict, _ = scan(serialize(first) + serialize(again), None)
    assert verdict.codes == ["DUPLICATE_FREEZE"] and "DEMO_D001 version 1" in verdict.violations[0].message


def test_missing_sources_message_names_the_field() -> None:
    first = freeze_entry()
    second = make_entry(seq=1, prev=first["hash"], ts=ts(1), type="record", body=record_body(sources=[]))
    verdict, _ = scan(serialize(first) + serialize(second), None)
    assert verdict.codes == ["MISSING_FIELD"] and "sources" in verdict.violations[0].message
