# SPDX-License-Identifier: Apache-2.0
"""Mutated ledgers must always fail verification with the right code family and never raise."""

from __future__ import annotations

import json
from typing import Any

import pytest
from hardening_support import build_sample_ledger, record_body
from hypothesis import given
from hypothesis import strategies as st

from protocolith.core import decode, encode, scan
from protocolith.core.issue import card_hash
from protocolith.core.ledger import ZERO_HASH, entry_hash

DOCUMENTED = {
    "BAD_SEQ", "BAD_PREV", "BAD_HASH", "NOT_CANONICAL", "TS_REGRESSION", "UNKNOWN_PROTOCOL", "DUPLICATE_FREEZE",
    "BAD_STATUS", "MISSING_FIELD", "DANGLING_REF", "BAD_CARD", "UNKNOWN_VERSION", "TRUNCATED_TAIL",
    "ENTRY_TOO_LARGE", "TOO_DEEP", "BAD_ENTRY",
}  # fmt: skip


@pytest.fixture(scope="module")
def good(tmp_path_factory: pytest.TempPathFactory) -> bytes:
    data = build_sample_ledger(tmp_path_factory.mktemp("sample") / "store")
    assert scan(data, card_hash)[0].ok
    return data


def verdict_of(data: bytes) -> Any:
    verdict, _ = scan(data, card_hash)
    assert set(verdict.codes) <= DOCUMENTED, verdict.codes
    assert verdict.ok == (not verdict.violations)
    encode(verdict.to_dict())  # always serializable
    return verdict


def line_prefixes(data: bytes) -> set[bytes]:
    lines = data.splitlines(keepends=True)
    return {b"".join(lines[:i]) for i in range(len(lines) + 1)}


def test_sample_is_valid_and_covers_every_type(good: bytes) -> None:
    types = [decode(line)["type"] for line in good.splitlines()]
    assert sorted(set(types)) == ["deviation", "freeze", "issue", "record"]


@given(st.data())
def test_any_byte_mutation_is_detected(good: bytes, data: st.DataObject) -> None:
    raw = bytearray(good)
    for _ in range(data.draw(st.integers(1, 3))):
        pos = data.draw(st.integers(0, len(raw) - 1))
        raw[pos] ^= data.draw(st.integers(1, 255))
    mutated = bytes(raw)
    verdict = verdict_of(mutated)
    # Flipping bytes can never turn the ledger into another valid ledger unless it restores the original.
    assert verdict.ok == (mutated == good)


@given(st.integers(0, 10_000))
def test_truncation_anywhere(good: bytes, cut: int) -> None:
    cut %= len(good) + 1
    mutated = good[:cut]
    verdict = verdict_of(mutated)
    if mutated in line_prefixes(good):
        assert verdict.ok and verdict.count == mutated.count(b"\n")
    else:
        assert verdict.codes == ["TRUNCATED_TAIL"]
        assert verdict.count == mutated.count(b"\n")


@given(st.data())
def test_line_surgery(good: bytes, data: st.DataObject) -> None:
    lines = good.splitlines(keepends=True)
    n = len(lines)
    op = data.draw(st.sampled_from(["delete", "duplicate", "swap", "insert_copy", "insert_garbage", "reverse"]))
    i = data.draw(st.integers(0, n - 1))
    j = data.draw(st.integers(0, n - 1))
    out = list(lines)
    if op == "delete":
        del out[i]
    elif op == "duplicate":
        out.insert(i, lines[i])
    elif op == "swap":
        out[i], out[j] = out[j], out[i]
    elif op == "insert_copy":
        out.insert(j, lines[i])
    elif op == "insert_garbage":
        out.insert(j, data.draw(st.sampled_from([b"\n", b"{}\n", b"[1]\n", b"garbage\n", b'{"seq":0}\n'])))
    else:
        out.reverse()
    mutated = b"".join(out)
    verdict = verdict_of(mutated)
    # Only removing a suffix of whole lines (or an identity edit) can leave a valid ledger.
    assert verdict.ok == (mutated in line_prefixes(good))
    if not verdict.ok and op in {"delete", "duplicate", "insert_copy"} and mutated.endswith(b"\n"):
        assert {"BAD_SEQ", "BAD_PREV", "BAD_ENTRY", "TRUNCATED_TAIL", "DUPLICATE_FREEZE", "TS_REGRESSION"} & set(
            verdict.codes
        )


def edited(good: bytes, index: int, change: dict[str, Any], *, rehash: bool) -> bytes:
    lines = good.splitlines()
    entry = decode(lines[index])
    entry.update(change)
    if rehash:
        entry["hash"] = entry_hash(entry)
    lines[index] = encode(entry)
    return b"\n".join(lines) + b"\n"


@given(st.data())
def test_field_changes_give_the_matching_code(good: bytes, data: st.DataObject) -> None:
    count = good.count(b"\n")
    index = data.draw(st.integers(0, count - 1))
    original = decode(good.splitlines()[index])
    field = data.draw(st.sampled_from(["seq", "prev", "hash", "ts", "type"]))
    other_hash = data.draw(st.text("0123456789abcdef", min_size=64, max_size=64).filter(lambda h: h not in (original["prev"], original["hash"])))
    # A rehashed ts/type edit on the last line has no successor to expose it, so it is only checked for ts regression.
    last = index == count - 1
    if field == "seq":
        value: Any = data.draw(st.integers(0, 50).filter(lambda s: s != index))
        verdict = verdict_of(edited(good, index, {"seq": value}, rehash=True))
        assert "BAD_SEQ" in verdict.codes
        verdict = verdict_of(edited(good, index, {"seq": value}, rehash=False))
        assert {"BAD_SEQ", "BAD_HASH"} <= set(verdict.codes)
    elif field == "prev":
        verdict = verdict_of(edited(good, index, {"prev": other_hash}, rehash=True))
        assert "BAD_PREV" in verdict.codes
        assert "BAD_PREV" in verdict_of(edited(good, index, {"prev": ZERO_HASH if index else other_hash}, rehash=True)).codes
    elif field == "hash":
        verdict = verdict_of(edited(good, index, {"hash": other_hash}, rehash=False))
        assert "BAD_HASH" in verdict.codes
        assert verdict.violations[0].seq == index or index == 0 or verdict.violations[0].seq <= index
        assert ("BAD_PREV" in verdict.codes) == (not last)
    elif field == "ts":
        stamp = data.draw(st.sampled_from(["2026-11-15T09:59:59Z", "2027-01-01T00:00:00Z", "1999-12-31T23:59:59Z"]))
        verdict = verdict_of(edited(good, index, {"ts": stamp}, rehash=False))
        assert "BAD_HASH" in verdict.codes
        verdict = verdict_of(edited(good, index, {"ts": stamp}, rehash=True))
        if stamp < "2026-11-15T10:00:00Z":
            assert "TS_REGRESSION" in verdict.codes or index == 0
            assert not verdict.ok
        elif not last:
            assert not verdict.ok  # either TS_REGRESSION on a later line or BAD_PREV
    else:
        kind = data.draw(st.sampled_from(["freeze", "record", "deviation", "issue", "bogus"]).filter(lambda t: t != original["type"]))
        verdict = verdict_of(edited(good, index, {"type": kind}, rehash=True))
        assert not verdict.ok
        assert {"BAD_ENTRY", "MISSING_FIELD"} & set(verdict.codes)


def test_unknown_version_and_extra_keys(good: bytes) -> None:
    assert "UNKNOWN_VERSION" in verdict_of(edited(good, 0, {"v": 2}, rehash=True)).codes
    assert "UNKNOWN_VERSION" in verdict_of(edited(good, 0, {"v": True}, rehash=True)).codes
    assert "BAD_ENTRY" in verdict_of(edited(good, 0, {"extra": 1}, rehash=True)).codes


def test_crlf_and_spaced_ledger_do_not_verify(good: bytes) -> None:
    crlf = good.replace(b"\n", b"\r\n")
    assert "NOT_CANONICAL" in verdict_of(crlf).codes
    spaced = b"".join(json.dumps(decode(line)).encode() + b"\n" for line in good.splitlines())
    assert "NOT_CANONICAL" in verdict_of(spaced).codes
    assert verdict_of(b"\xef\xbb\xbf" + good).ok is False


@given(st.binary(max_size=400))
def test_scan_arbitrary_bytes_never_raises(blob: bytes) -> None:
    verdict = verdict_of(blob)
    assert verdict.count == blob.count(b"\n")


@given(st.lists(st.sampled_from([b'{"a":1}', b"[]", b"", b"x", b'{"seq":0}', b'{"v":1}']), max_size=8))
def test_scan_line_soup(lines: list[bytes]) -> None:
    verdict = verdict_of(b"".join(line + b"\n" for line in lines))
    assert (not lines) == verdict.ok  # no line here is a valid entry


CARD_JUNK = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(-5, 5), st.text(max_size=6)),
    lambda inner: st.one_of(st.lists(inner, max_size=3), st.dictionaries(st.text(max_size=6), inner, max_size=3)),
    max_leaves=6,
)


@given(st.dictionaries(st.sampled_from(["operator", "domain", "known_limitations", "verification_count", "raw_payload_committed", "claim_boundary", "sources", "x"]), CARD_JUNK, max_size=5))
def test_hostile_card_metadata_never_crashes_verify(tmp_path_factory: pytest.TempPathFactory, card: dict[str, Any]) -> None:
    """A record with arbitrary ``card`` content, followed by an issue entry, must verify to a verdict, not raise."""
    from hardening_support import PROTOCOL, PROTOCOL_SHA, ts

    from protocolith.core.ledger import make_entry, serialize

    freeze_body = {"protocol_id": "DEMO_D001", "protocol": PROTOCOL, "protocol_sha256": PROTOCOL_SHA, "supersedes": None, "version": "1"}
    first = make_entry(seq=0, prev=ZERO_HASH, ts=ts(0), type="freeze", body=freeze_body)
    second = make_entry(seq=1, prev=first["hash"], ts=ts(1), type="record", body=record_body(card=card))
    body = {"card_sha256": "c" * 64, "format": "evidence-card-json-svg", "record_seq": 1}
    third = make_entry(seq=2, prev=second["hash"], ts=ts(2), type="issue", body=body)
    verdict = verdict_of(b"".join(serialize(e) for e in (first, second, third)))
    assert not verdict.ok  # the card hash "ccc..." can never match
