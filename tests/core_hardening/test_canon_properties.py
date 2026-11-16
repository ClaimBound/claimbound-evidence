# SPDX-License-Identifier: Apache-2.0
"""Property, fuzz and differential tests for PCJ-1 (encode, decode, hash)."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

import pytest
from hardening_support import oracle_bytes
from hypothesis import example, given
from hypothesis import strategies as st

from protocolith.core import CanonError, decode, encode, sha256_hex
from protocolith.core.canonical import MAX_DEPTH, MAX_INT

CODES = {
    "BAD_JSON", "BAD_UTF8", "BAD_TYPE", "FLOAT_NOT_ALLOWED", "NON_FINITE", "INT_RANGE",
    "DUPLICATE_KEY", "LONE_SURROGATE", "TOO_DEEP",
}  # fmt: skip

TEXT = st.text()  # Hypothesis text never contains lone surrogates
INTS = st.one_of(st.integers(-MAX_INT, MAX_INT), st.sampled_from([0, -1, 1, MAX_INT, -MAX_INT]))
SCALARS = st.one_of(st.none(), st.booleans(), INTS, TEXT)
VALUES = st.recursive(
    SCALARS,
    lambda inner: st.one_of(st.lists(inner, max_size=5), st.dictionaries(TEXT, inner, max_size=5)),
    max_leaves=25,
)


def same(a: Any, b: Any) -> bool:
    """Equality that distinguishes bool from int and ignores dict order."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)


@given(VALUES)
@example({"": [], "\x00": "\x1f\x7f \U0001f600", "b": -MAX_INT})
def test_round_trip_and_idempotence(value: Any) -> None:
    data = encode(value)
    back = decode(data)
    assert same(back, value)
    assert encode(back) == data
    assert decode(data.decode("utf-8")) == back


@given(VALUES)
def test_differential_oracle(value: Any) -> None:
    """The encoder equals json.dumps(sort_keys, compact, ensure_ascii=False) on the whole PCJ-1 domain."""
    assert encode(value) == oracle_bytes(value)


@given(VALUES, st.booleans(), st.sampled_from([None, 0, 1, 4, "\t"]), st.booleans())
def test_decode_ignores_layout(value: Any, ensure_ascii: bool, indent: Any, sort_keys: bool) -> None:
    """Any JSON layout of a value canonicalizes to the same bytes (escapes, whitespace, key order)."""
    text = json.dumps(value, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys)
    assert encode(decode(text)) == oracle_bytes(value)
    assert encode(decode(text.encode("utf-8"))) == oracle_bytes(value)


@given(VALUES, st.randoms(use_true_random=False))
def test_hash_stable_under_key_order(value: Any, rnd: random.Random) -> None:
    def shuffled(item: Any) -> Any:
        if isinstance(item, dict):
            keys = list(item)
            rnd.shuffle(keys)
            return {key: shuffled(item[key]) for key in keys}
        if isinstance(item, list):
            return [shuffled(x) for x in item]
        return item

    digest = sha256_hex(value)
    assert digest == sha256_hex(shuffled(value))
    assert digest == hashlib.sha256(oracle_bytes(value)).hexdigest()
    assert len(digest) == 64 and digest == digest.lower()


@given(VALUES, VALUES)
def test_hash_distinguishes_values(a: Any, b: Any) -> None:
    if not same(a, b):
        assert sha256_hex(a) != sha256_hex(b)


def test_golden_hashes() -> None:
    """Pinned digests, computed independently, catch any accidental change of the byte format."""
    assert sha256_hex({}) == hashlib.sha256(b"{}").hexdigest()
    assert sha256_hex({"b": [1, "é"], "a": None}) == hashlib.sha256('{"a":null,"b":[1,"é"]}'.encode()).hexdigest()
    assert encode("\x00\x1f\x7f퟿\U0010ffff") == '"\\u0000\\u001f\x7f퟿\U0010ffff"'.encode()


def test_bool_is_not_int_and_int_not_bool() -> None:
    assert encode([True, False, 1, 0]) == b"[true,false,1,0]"
    assert decode("[true,1]") == [True, 1]
    assert type(decode("[true]")[0]) is bool


# --- the parser never raises anything but CanonError -------------------------------------------------

ALPHABET = list('[]{}",:0123456789.-+eEtrufalsnNIiy\\ \n\t/bu') + ["\\u", "\\ud800", "null", "true", "NaN", "Infinity", "-0"]
SOUP = st.lists(st.sampled_from(ALPHABET), max_size=40).map("".join)
ANY_CODEPOINTS = st.lists(st.integers(0, 0x10FFFF).map(chr), max_size=30).map("".join)  # includes surrogates


def assert_decodes_or_documented_error(data: bytes | str) -> None:
    try:
        value = decode(data)
    except CanonError as exc:
        assert exc.code in CODES
        assert exc.exit_code == 2
        exc.message.encode("utf-8")  # messages stay encodable
        return
    out = encode(value)
    assert decode(out) == value
    assert out == oracle_bytes(value)


@given(st.binary(max_size=200))
@example(b"\xef\xbb\xbf{}")
@example(b"\xff")
@example(b'"\xed\xa0\x80"')  # UTF-8 encoded surrogate
def test_parser_arbitrary_bytes(data: bytes) -> None:
    assert_decodes_or_documented_error(data)


@given(st.one_of(st.text(max_size=100), ANY_CODEPOINTS, SOUP))
@example("\ud800")
@example('"\\ud800"')
@example("٣")  # a non-ASCII digit must not parse as a number
@example("[" * 5000)
def test_parser_arbitrary_text(text: str) -> None:
    assert_decodes_or_documented_error(text)


@given(VALUES, st.data())
def test_parser_mutated_valid_json(value: Any, data: st.DataObject) -> None:
    raw = bytearray(encode(value))
    for _ in range(data.draw(st.integers(1, 3))):
        pos = data.draw(st.integers(0, len(raw)))
        action = data.draw(st.sampled_from(["flip", "insert", "delete"]))
        if action == "flip" and raw:
            raw[min(pos, len(raw) - 1)] ^= data.draw(st.integers(1, 255))
        elif action == "insert":
            raw.insert(pos, data.draw(st.integers(0, 255)))
        elif raw:
            del raw[min(pos, len(raw) - 1)]
    assert_decodes_or_documented_error(bytes(raw))


PY_JUNK = st.recursive(
    st.one_of(
        SCALARS,
        st.floats(),
        st.binary(max_size=4),
        st.integers(),
        st.just(object()),
        st.complex_numbers(),
        st.text(alphabet=st.sampled_from(["a", "\ud800", "\udfff"])),
    ),
    lambda inner: st.one_of(
        st.lists(inner, max_size=4),
        st.tuples(inner),
        st.sets(st.integers(), max_size=2),
        st.dictionaries(st.one_of(TEXT, st.integers(), st.none(), st.tuples(st.integers())), inner, max_size=4),
        st.dictionaries(TEXT, inner, max_size=4),
    ),
    max_leaves=15,
)


@given(PY_JUNK)
def test_encoder_arbitrary_python_objects(value: Any) -> None:
    try:
        out = encode(value)
    except CanonError as exc:
        assert exc.code in CODES
        return
    assert out == oracle_bytes(value)
    assert same(decode(out), value)


@given(st.integers())
def test_integer_range_edges(n: int) -> None:
    if abs(n) <= MAX_INT:
        assert encode(n) == str(n).encode()
        assert decode(str(n)) == n
    else:
        for call in (lambda: encode(n), lambda: decode(str(n))):
            with pytest.raises(CanonError) as info:
                call()
            assert info.value.code == "INT_RANGE"


@given(st.integers(1, 200))
def test_depth_boundary(depth: int) -> None:
    text = "[" * depth + "]" * depth
    if depth <= MAX_DEPTH:
        assert encode(decode(text)) == text.encode()
    else:
        with pytest.raises(CanonError) as info:
            decode(text)
        assert info.value.code == "TOO_DEEP"
    obj = "".join('{"a":' for _ in range(depth)) + "1" + "}" * depth
    if depth <= MAX_DEPTH:
        assert encode(decode(obj)) == obj.encode()
    else:
        with pytest.raises(CanonError):
            decode(obj)
