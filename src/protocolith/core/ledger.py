# SPDX-License-Identifier: Apache-2.0
"""Ledger entry format: constants, hashing and serialization."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .canonical import encode, sha256_hex
from .errors import InputError

FORMAT_VERSION = 1
ZERO_HASH = "0" * 64
MAX_ENTRY_BYTES = 1_048_576
ENTRY_TYPES = ("freeze", "record", "deviation", "issue")
ENTRY_KEYS = frozenset({"body", "hash", "prev", "seq", "ts", "type", "v"})
CARD_FORMAT = "evidence-card-json-svg"

# Same closed sets as protocolith.evidence_card; a test keeps them identical.
RESULT_STATUSES = frozenset(
    {
        "PASSED_UNDER_PROTOCOL",
        "NEGATIVE_RESULT_UNDER_PROTOCOL",
        "BLOCKED_SOURCE",
        "INSUFFICIENT_COVERAGE",
        "SOURCE_DRIFT",
        "REPRODUCED_OUTCOME",
    }
)

Entry = dict[str, Any]

_HASH_RE = re.compile(r"[0-9a-f]{64}")
_HEAD_REF_RE = re.compile(r"(0|[1-9][0-9]*):([0-9a-f]{64})")
_TS_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


def is_hash(value: object) -> bool:
    return isinstance(value, str) and _HASH_RE.fullmatch(value) is not None


def parse_head_ref(value: object) -> tuple[int, str]:
    """Parse ``SEQ:HASH`` (decimal seq without leading zeros, lowercase 64-hex hash)."""
    found = _HEAD_REF_RE.fullmatch(value) if isinstance(value, str) else None
    if found is None:
        raise InputError("BAD_ENTRY", "expected head must look like SEQ:HASH (decimal seq, 64 lowercase hex characters)")
    return int(found.group(1)), found.group(2)


def is_ts(value: object) -> bool:
    if not (isinstance(value, str) and _TS_RE.fullmatch(value)):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def entry_hash(entry: Mapping[str, Any]) -> str:
    """sha256 of the entry object without its ``hash`` field."""
    return sha256_hex({key: value for key, value in entry.items() if key != "hash"})


def make_entry(*, seq: int, prev: str, ts: str, type: str, body: Mapping[str, Any]) -> Entry:
    entry: Entry = {"body": body, "prev": prev, "seq": seq, "ts": ts, "type": type, "v": FORMAT_VERSION}
    entry["hash"] = entry_hash(entry)
    return entry


def serialize(entry: Mapping[str, Any]) -> bytes:
    """One ledger line: PCJ-1 bytes plus a newline."""
    return encode(entry) + b"\n"
