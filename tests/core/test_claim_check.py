# SPDX-License-Identifier: Apache-2.0
"""claim_check: what an agent may and may not say, computed from the ledger."""

from __future__ import annotations

import pytest
from core_support import NOW, PROTOCOL_SHA, clock, deviation_body, protocol, record_body

from protocolith.core import InputError, ProtocolithError, Store, VerificationFailed, anchor_head, claim_check, deviation, freeze, record

LATER = "2026-11-15T10:00:05Z"


def test_a_passed_record_frozen_earlier(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(), clock=clock(LATER))
    found = claim_check(store, seq=1)
    assert found["supported"] is True and found["status"] == "PASSED_UNDER_PROTOCOL" and found["seq"] == 1
    assert found["protocol_frozen_before_record"] is True and found["deviations"] == 0
    assert found["anchored"] is False and found["independent_reproduction"] is False
    assert found["sources"] == [{"id": "source-1", "sha256": "a" * 64}]
    assert found["protocol_id"] == "DEMO_D001" and found["protocol_version"] == "1" and found["protocol_sha256"] == PROTOCOL_SHA
    assert found["may_say"] == (
        "Under protocol DEMO_D001 version 1, run run-1 passed its gate; this holds only within this boundary: "
        "Only the stated gate on the stated source and period."
    )
    assert found["must_not_say"] == ["independently reproduced", "externally anchored", "applies beyond the claim boundary"]
    assert claim_check(store, protocol="DEMO_D001") == found


def test_same_second_freeze_is_not_shown_to_be_earlier(recorded: Store) -> None:
    found = claim_check(recorded, seq=1)
    assert found["protocol_frozen_before_record"] is False
    assert found["must_not_say"][1:3] == ["prospective", "preregistered"]


def test_anchoring_deviations_and_reproduction(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    deviation(store, deviation_body(), clock=clock(NOW))
    record(store, record_body(deviations=[1]), clock=clock(LATER))
    assert claim_check(store, seq=2)["anchored"] is False
    anchor_head(store, clock=clock(LATER))
    record(store, record_body(run_id="run-2", status="REPRODUCED_OUTCOME"), clock=clock(LATER))
    first, second = claim_check(store, seq=2), claim_check(store, seq=3)
    assert first["anchored"] is True and second["anchored"] is False
    assert first["deviations"] == 1 and "followed the protocol without deviations" in first["must_not_say"]
    assert first["independent_reproduction"] is True and second["independent_reproduction"] is True
    assert "independently reproduced" not in second["must_not_say"]
    assert second["may_say"].startswith("Under protocol DEMO_D001 version 1, run run-2 reproduced an earlier outcome;")
    assert claim_check(store, protocol="DEMO_D001")["seq"] == 3


@pytest.mark.parametrize(
    ("status", "extra", "phrase"),
    [
        ("NEGATIVE_RESULT_UNDER_PROTOCOL", {}, "did not meet its gate (a negative result under the protocol)"),
        ("BLOCKED_SOURCE", {"block_reason": "HTTP 403"}, "was blocked because a required source was not available"),
        ("INSUFFICIENT_COVERAGE", {}, "had insufficient coverage"),
        ("SOURCE_DRIFT", {"drift_reason": "the page changed"}, "saw its source change during the run"),
    ],
)
def test_other_statuses(store: Store, status: str, extra: dict[str, str], phrase: str) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(status=status, **extra), clock=clock(LATER))
    found = claim_check(store, seq=1)
    assert phrase in found["may_say"]
    if status == "NEGATIVE_RESULT_UNDER_PROTOCOL":
        assert found["supported"] is True and "negative result" not in found["must_not_say"]
    else:
        assert found["supported"] is False
        assert "no result was obtained and none may be inferred" in found["may_say"]
        assert {"negative result", "positive result"} <= set(found["must_not_say"])


def test_protocol_without_a_record_supports_nothing(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    found = claim_check(store, protocol="DEMO_D001")
    assert found["supported"] is False and found["seq"] is None and found["status"] is None and found["sources"] == []
    assert found["may_say"] == "No result is recorded for protocol DEMO_D001 version 1; nothing may be reported as a result."
    assert "any result" in found["must_not_say"] and found["protocol_sha256"] == PROTOCOL_SHA


def test_bad_arguments(recorded: Store) -> None:
    for kwargs, code in (
        ({}, "BAD_ENTRY"),
        ({"seq": 1, "protocol": "DEMO_D001"}, "BAD_ENTRY"),
        ({"seq": 0}, "DANGLING_REF"),
        ({"seq": 99}, "DANGLING_REF"),
        ({"seq": True}, "DANGLING_REF"),
        ({"seq": "1"}, "DANGLING_REF"),
        ({"protocol": "NOPE"}, "UNKNOWN_PROTOCOL"),
    ):
        with pytest.raises(InputError) as info:
            claim_check(recorded, **kwargs)  # type: ignore[arg-type]
        assert info.value.code == code, kwargs


def test_an_unverifiable_ledger_supports_nothing(recorded: Store) -> None:
    recorded.ledger_path.write_bytes(recorded.ledger_path.read_bytes().replace(b"run-1", b"run-9"))
    with pytest.raises(VerificationFailed):
        claim_check(recorded, seq=1)
    with pytest.raises(ProtocolithError):
        claim_check(Store(recorded.path / "missing"), seq=1)


def test_mismatching_anchor_does_not_count(recorded: Store) -> None:
    anchor_head(recorded, clock=clock())
    data = recorded.ledger_path.read_bytes()
    assert claim_check(recorded, seq=1)["anchored"] is True
    from protocolith.core import verify_anchors

    # replace the anchored entry consistently: the anchor no longer matches, so the record is not anchored
    import json

    from protocolith.core.ledger import make_entry, serialize

    lines = [json.loads(line) for line in data.splitlines()]
    body = dict(lines[1]["body"])
    body["outcome"] = {"pass_rate": "0.99"}
    rebuilt = make_entry(seq=1, prev=lines[0]["hash"], ts=lines[1]["ts"], type="record", body=body)
    recorded.ledger_path.write_bytes(serialize(lines[0]) + serialize(rebuilt))
    assert [v.code for v in verify_anchors(recorded).violations] == ["ANCHOR_MISMATCH"]
    assert claim_check(recorded, seq=1)["anchored"] is False
