# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Any

from core_support import HASH_A, NOW, PROTOCOL_SHA, deviation_body, protocol, record_body

from protocolith.core import RESULT_STATUSES, Verdict, Verifier, encode, scan, sha256_hex
from protocolith.core.ledger import ZERO_HASH, make_entry, serialize
from protocolith.evidence_card import ALLOWED_RESULT_STATUSES, ALLOWED_REPRODUCTION_LEVELS


def freeze_body(proto: dict[str, Any], supersedes: str | None = None) -> dict[str, Any]:
    return {
        "protocol_id": proto["protocol_id"],
        "protocol": proto,
        "protocol_sha256": sha256_hex(proto),
        "supersedes": supersedes,
        "version": proto["version"],
    }


def build(*items: tuple[str, dict[str, Any]]) -> bytes:
    out = b""
    prev = ZERO_HASH
    for index, (kind, body) in enumerate(items):
        entry = make_entry(seq=index, prev=prev, ts=NOW, type=kind, body=body)
        out += serialize(entry)
        prev = entry["hash"]
    return out


def codes(data: bytes) -> list[str]:
    return scan(data)[0].codes


def test_status_set_matches_the_card_validator() -> None:
    assert RESULT_STATUSES == ALLOWED_RESULT_STATUSES
    assert "not independently reproduced" in ALLOWED_REPRODUCTION_LEVELS


def test_valid_ledger_and_verdict_shape() -> None:
    data = build(("freeze", freeze_body(protocol())), ("record", record_body()))
    verdict, verifier = scan(data)
    assert isinstance(verdict, Verdict)
    assert verdict.ok and verdict.count == 2 and verdict.head_seq == 1
    assert verdict.head_hash == verifier.tip_hash
    assert verdict.to_dict()["head"] == {"hash": verdict.head_hash, "seq": 1}


def test_empty_ledger_has_no_head() -> None:
    verdict, verifier = scan(b"")
    assert verdict.ok and verdict.count == 0 and verdict.head_hash is None and verdict.head_seq is None
    assert verifier.tip_hash == ZERO_HASH


def test_supersedes_must_name_the_same_protocol_id() -> None:
    old = protocol()
    other = {"protocol_id": "OTHER_D001", "version": "1"}
    new = {**old, "version": "2"}
    good = build(("freeze", freeze_body(old)), ("freeze", freeze_body(new, sha256_hex(old))))
    assert codes(good) == []
    wrong = build(("freeze", freeze_body(other)), ("freeze", freeze_body(new, sha256_hex(other))))
    assert codes(wrong) == ["UNKNOWN_PROTOCOL"]


def test_protocol_id_and_version_must_match_the_protocol() -> None:
    body = freeze_body(protocol())
    body["version"] = "9"
    assert codes(build(("freeze", body))) == ["BAD_ENTRY"]


def test_bad_protocol_id_characters() -> None:
    proto = {"protocol_id": "../x", "version": "1"}
    assert codes(build(("freeze", freeze_body(proto)))) == ["BAD_ENTRY"]


def test_issue_without_card_hasher_skips_r9() -> None:
    data = build(
        ("freeze", freeze_body(protocol())),
        ("record", record_body()),
        ("issue", {"card_sha256": HASH_A, "format": "evidence-card-json-svg", "record_seq": 1}),
    )
    assert codes(data) == []


def test_issue_bad_format_and_card_hash_shape() -> None:
    data = build(
        ("freeze", freeze_body(protocol())),
        ("record", record_body()),
        ("issue", {"card_sha256": "xyz", "format": "pdf", "record_seq": 1}),
    )
    assert codes(data) == ["BAD_ENTRY"]


def test_record_extra_field_and_wrong_types() -> None:
    base = [("freeze", freeze_body(protocol()))]
    assert codes(build(*base, ("record", record_body(surprise=1)))) == ["BAD_ENTRY"]
    assert codes(build(*base, ("record", record_body(deviations=[True])))) == ["BAD_ENTRY"]
    assert codes(build(*base, ("record", record_body(sources=[{"id": "x"}])))) == ["BAD_ENTRY"]
    assert codes(build(*base, ("record", record_body(block_reason="   ")))) == ["BAD_ENTRY"]
    assert codes(build(*base, ("record", record_body(status=5)))) == ["BAD_STATUS"]
    assert codes(build(*base, ("record", record_body(status="")))) == ["MISSING_FIELD"]


def test_dangling_reference_to_a_malformed_entry() -> None:
    bad_dev = {"kind": "x"}
    data = build(
        ("freeze", freeze_body(protocol())),
        ("deviation", bad_dev),
        ("record", record_body(deviations=[1])),
    )
    assert codes(data) == ["DANGLING_REF", "MISSING_FIELD"]


def test_deviation_unknown_protocol_and_field_problems() -> None:
    assert codes(build(("deviation", deviation_body()))) == ["UNKNOWN_PROTOCOL"]


def test_structure_errors_in_the_entry() -> None:
    entry = make_entry(seq=0, prev=ZERO_HASH, ts=NOW, type="freeze", body={})
    bad_type = {**entry, "type": "nope"}
    assert codes(encode(bad_type) + b"\n") == ["BAD_ENTRY"]
    assert codes(encode([1]) + b"\n" + encode([2]) + b"\n") == ["BAD_ENTRY"]


def test_unparseable_last_line_is_a_truncated_tail_unless_too_deep() -> None:
    found = Verifier().feed(b"not json", last=True)
    assert [v.code for v in found] == ["TRUNCATED_TAIL"]
    tail_deep = Verifier().feed(b"[" * 70 + b"]" * 70, last=True)
    assert [v.code for v in tail_deep] == ["TOO_DEEP"]


def test_violation_to_dict() -> None:
    found = Verifier().feed(b"[1]")
    assert found[0].to_dict() == {"code": "BAD_ENTRY", "message": "entry is not an object", "seq": 0}


def test_protocol_sha_constant() -> None:
    assert PROTOCOL_SHA == sha256_hex(protocol())
