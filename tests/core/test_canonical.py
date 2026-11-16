# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
from typing import Any

import pytest

from protocolith.core import CanonError, decode, encode, sha256_hex


def code_of(call: Any, *args: Any) -> str:
    with pytest.raises(CanonError) as info:
        call(*args)
    return str(info.value.code)


def test_scalars_and_containers() -> None:
    assert encode(None) == b"null"
    assert encode(True) == b"true"
    assert encode(False) == b"false"
    assert encode(0) == b"0"
    assert encode(-7) == b"-7"
    assert encode("a") == b'"a"'
    assert encode([]) == b"[]"
    assert encode({}) == b"{}"
    assert encode({"b": [1, {"z": None, "a": True}], "a": "x"}) == b'{"a":"x","b":[1,{"a":true,"z":null}]}'


def test_bool_is_not_an_integer_in_output() -> None:
    assert encode([True, 1]) == b"[true,1]"


def test_string_escapes() -> None:
    assert encode('"\\\b\f\n\r\t') == b'"\\"\\\\\\b\\f\\n\\r\\t"'
    assert encode("\x00\x1f\x07") == b'"\\u0000\\u001f\\u0007"'
    assert encode("\x7fé \U0001f600") == '"\x7fé \U0001f600"'.encode()


def test_keys_sorted_by_code_point() -> None:
    assert encode({"\U00010000": 1, "￿": 2}).decode() == '{"￿":2,"\U00010000":1}'


def test_integer_bounds() -> None:
    assert encode(2**53 - 1) == b"9007199254740991"
    assert encode(-(2**53 - 1)) == b"-9007199254740991"
    assert code_of(encode, 2**53) == "INT_RANGE"
    assert code_of(encode, -(2**53)) == "INT_RANGE"


def test_encode_rejections() -> None:
    assert code_of(encode, 1.5) == "FLOAT_NOT_ALLOWED"
    assert code_of(encode, float("nan")) == "FLOAT_NOT_ALLOWED"
    assert code_of(encode, "\ud800") == "LONE_SURROGATE"
    assert code_of(encode, (1, 2)) == "BAD_TYPE"
    assert code_of(encode, {1: 2}) == "BAD_TYPE"
    assert code_of(encode, b"x") == "BAD_TYPE"


def test_depth_limit() -> None:
    value: Any = []
    for _ in range(63):
        value = [value]
    assert encode(value) == b"[" * 64 + b"]" * 64
    assert code_of(encode, [value]) == "TOO_DEEP"
    assert code_of(encode, {"a": [value]}) == "TOO_DEEP"


def test_decode_round_trip_and_whitespace() -> None:
    assert decode(b' {"b" : 1,\n "a":[2, null, true]} ') == {"a": [2, None, True], "b": 1}
    assert decode('"\\ud83d\\ude00"') == "\U0001f600"
    assert decode("-0") == 0


def test_decode_errors() -> None:
    assert code_of(decode, b'{"a":1,"a":2}') == "DUPLICATE_KEY"
    assert code_of(decode, "1.0") == "FLOAT_NOT_ALLOWED"
    assert code_of(decode, "1e3") == "FLOAT_NOT_ALLOWED"
    assert code_of(decode, "NaN") == "NON_FINITE"
    assert code_of(decode, "[Infinity]") == "NON_FINITE"
    assert code_of(decode, "9007199254740992") == "INT_RANGE"
    assert code_of(decode, "1" + "0" * 40) == "INT_RANGE"
    assert code_of(decode, '"\\ud800"') == "LONE_SURROGATE"
    assert code_of(decode, b"\xef\xbb\xbf{}") == "BAD_JSON"
    assert code_of(decode, b'"\xff"') == "BAD_UTF8"
    assert code_of(decode, "") == "BAD_JSON"
    assert code_of(decode, "{} x") == "BAD_JSON"
    assert code_of(decode, "[" * 65 + "]" * 65) == "TOO_DEEP"
    assert code_of(decode, "[" * 100000 + "]" * 100000) == "TOO_DEEP"


def test_decode_error_message_names_the_key() -> None:
    with pytest.raises(CanonError, match="'dup'"):
        decode('{"dup":1,"dup":2}')


def test_sha256_is_over_canonical_bytes() -> None:
    assert sha256_hex({"b": 1, "a": 2}) == hashlib.sha256(b'{"a":2,"b":1}').hexdigest()
    assert sha256_hex({}) == "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
