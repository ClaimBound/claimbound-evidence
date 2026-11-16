# SPDX-License-Identifier: Apache-2.0
"""PCJ-1 canonical JSON: encode, strict decode and sha256."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .errors import InputError

MAX_DEPTH = 64
MAX_INT = 2**53 - 1
_MAX_INT_CHARS = 32

_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_NEEDS_ESCAPE = re.compile('[\x00-\x1f"\\\\]')


class CanonError(InputError):
    """Input that is not valid PCJ-1 data."""


def _escape(match: re.Match[str]) -> str:
    char = match.group()
    return _ESCAPES.get(char) or f"\\u{ord(char):04x}"


def _enc_string(text: str) -> str:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise CanonError("LONE_SURROGATE", "string contains a lone surrogate") from None
    return '"' + _NEEDS_ESCAPE.sub(_escape, text) + '"'


def _enc_int(value: int) -> str:
    if abs(value) > MAX_INT:
        raise CanonError("INT_RANGE", f"integer outside +-(2^53-1): {value}")
    return str(value)


def _encode(value: object, depth: int) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return _enc_int(value)
    if isinstance(value, str):
        return _enc_string(value)
    if isinstance(value, float):
        raise CanonError("FLOAT_NOT_ALLOWED", "floats are not allowed; write decimals as strings")
    if isinstance(value, (list, dict)):
        if depth + 1 > MAX_DEPTH:
            raise CanonError("TOO_DEEP", f"nesting deeper than {MAX_DEPTH}")
        return _encode_container(value, depth + 1)
    raise CanonError("BAD_TYPE", f"unsupported type: {type(value).__name__}")


def _encode_container(value: list[Any] | dict[Any, Any], depth: int) -> str:
    if isinstance(value, list):
        return "[" + ",".join(_encode(item, depth) for item in value) + "]"
    if not all(isinstance(key, str) for key in value):
        raise CanonError("BAD_TYPE", "object keys must be strings")
    return "{" + ",".join(f"{_enc_string(key)}:{_encode(value[key], depth)}" for key in sorted(value)) + "}"


def encode(value: object) -> bytes:
    """Return the PCJ-1 bytes of ``value``."""
    return _encode(value, 0).encode("utf-8")


def sha256_hex(value: object) -> str:
    return hashlib.sha256(encode(value)).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, item in pairs:
        if key in seen:
            raise CanonError("DUPLICATE_KEY", f"duplicate key {key!r}")
        seen[key] = item
    return seen


def _no_float(text: str) -> Any:
    raise CanonError("FLOAT_NOT_ALLOWED", f"floats are not allowed: {text}; write decimals as strings")


def _no_constant(text: str) -> Any:
    raise CanonError("NON_FINITE", f"{text} is not allowed")


def _parse_int(text: str) -> int:
    if len(text) > _MAX_INT_CHARS:
        raise CanonError("INT_RANGE", "integer outside +-(2^53-1)")
    return int(text)


def decode(data: bytes | str) -> Any:
    """Strictly parse JSON: no duplicate keys, no floats, no BOM, depth and range limits."""
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8")
        except UnicodeDecodeError:
            raise CanonError("BAD_UTF8", "input is not valid UTF-8") from None
    try:
        value = json.loads(
            data,
            object_pairs_hook=_pairs,
            parse_float=_no_float,
            parse_constant=_no_constant,
            parse_int=_parse_int,
        )
    except json.JSONDecodeError as exc:
        raise CanonError("BAD_JSON", f"invalid JSON: {exc.msg} at char {exc.pos}") from None
    except RecursionError:
        raise CanonError("TOO_DEEP", f"nesting deeper than {MAX_DEPTH}") from None
    encode(value)  # validates ranges, surrogates and depth
    return value
