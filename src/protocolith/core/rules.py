# SPDX-License-Identifier: Apache-2.0
"""Ledger verification: rules R1 to R11 plus the size and depth limits."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial
from typing import Any

from .canonical import CanonError, decode, encode, sha256_hex
from .errors import ProtocolithError, Violation
from .ledger import (
    CARD_FORMAT,
    ENTRY_KEYS,
    ENTRY_TYPES,
    FORMAT_VERSION,
    MAX_ENTRY_BYTES,
    RESULT_STATUSES,
    ZERO_HASH,
    Entry,
    entry_hash,
    is_hash,
    is_ts,
)

Pred = Callable[[Any], bool]
Add = Callable[[str, str], None]
CardHasher = Callable[["Verifier", int], str]

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_VERSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}")
_BLOCKING = {"BLOCKED_SOURCE": "block_reason", "SOURCE_DRIFT": "drift_reason"}
_NEEDS_SOURCES = frozenset({"PASSED_UNDER_PROTOCOL", "NEGATIVE_RESULT_UNDER_PROTOCOL", "REPRODUCED_OUTCOME"})


def _text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _obj(value: Any) -> bool:
    return isinstance(value, dict)


def _uint(value: Any) -> bool:
    return type(value) is int and value >= 0


def _uint_list(value: Any) -> bool:
    return isinstance(value, list) and all(_uint(item) for item in value)


def _source(value: Any) -> bool:
    return bool(isinstance(value, dict) and set(value) == {"id", "sha256"} and _text(value["id"]) and is_hash(value["sha256"]))


def _sources(value: Any) -> bool:
    return isinstance(value, list) and all(_source(item) for item in value)


def _hash_or_null(value: Any) -> bool:
    return value is None or is_hash(value)


def _protocol_id(value: Any) -> bool:
    return isinstance(value, str) and _ID_RE.fullmatch(value) is not None


def _version(value: Any) -> bool:
    return isinstance(value, str) and _VERSION_RE.fullmatch(value) is not None


def _any(value: Any) -> bool:
    return True


def _is_format(value: Any) -> bool:
    return bool(value == CARD_FORMAT)


def _blank(value: Any) -> bool:
    return isinstance(value, str) and value.strip() == ""


FREEZE_FIELDS: dict[str, Pred] = {
    "protocol_id": _protocol_id,
    "version": _version,
    "protocol": _obj,
    "protocol_sha256": is_hash,
    "supersedes": _hash_or_null,
}
RECORD_FIELDS: dict[str, Pred] = {
    "protocol_sha256": is_hash,
    "run_id": _text,
    "status": _any,
    "outcome": _obj,
    "sources": _sources,
    "reproduction_level": _text,
    "claim_boundary": _text,
    "deviations": _uint_list,
}
RECORD_OPTIONAL: dict[str, Pred] = {"block_reason": _text, "drift_reason": _text, "card": _obj}
DEVIATION_FIELDS: dict[str, Pred] = {"protocol_sha256": is_hash, "kind": _text, "description": _text}
ISSUE_FIELDS: dict[str, Pred] = {"record_seq": _uint, "format": _is_format, "card_sha256": is_hash}
ENTRY_FIELDS: dict[str, Pred] = {
    "seq": _uint,
    "ts": is_ts,
    "prev": is_hash,
    "hash": is_hash,
    "type": lambda value: value in ENTRY_TYPES,
    "body": _obj,
}


def shape_problems(body: Entry, required: Mapping[str, Pred], optional: Mapping[str, Pred]) -> list[tuple[str, str]]:
    """Check field presence, type and closed key set of a body."""
    preds = {**required, **optional}
    missing = sorted(key for key in required if key not in body or _blank(body[key]))
    bad = sorted(key for key, value in body.items() if key in preds and key not in missing and not preds[key](value))
    extra = sorted(key for key in body if key not in preds)
    problems: list[tuple[str, str]] = []
    if missing:
        problems.append(("MISSING_FIELD", "missing fields: " + ", ".join(missing)))
    if bad or extra:
        problems.append(("BAD_ENTRY", f"invalid fields: {', '.join(bad)}; unexpected fields: {', '.join(extra)}"))
    return problems


@dataclass
class Verdict:
    ok: bool
    count: int
    head_seq: int | None
    head_hash: str | None
    violations: list[Violation]

    @property
    def codes(self) -> list[str]:
        return sorted({v.code for v in self.violations})

    def to_dict(self) -> dict[str, Any]:
        return {
            "codes": self.codes,
            "count": self.count,
            "head": {"hash": self.head_hash, "seq": self.head_seq},
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
        }


def _tip_of(obj: Any) -> str | None:
    return obj["hash"] if isinstance(obj, dict) and is_hash(obj.get("hash")) else None


def _structure(obj: Any) -> tuple[str, str] | None:
    if not isinstance(obj, dict):
        return ("BAD_ENTRY", "entry is not an object")
    if "v" in obj and not (type(obj["v"]) is int and obj["v"] == FORMAT_VERSION):
        return ("UNKNOWN_VERSION", f"unknown format version: {obj['v']!r}")
    if set(obj) != ENTRY_KEYS:
        return ("BAD_ENTRY", "entry keys must be exactly: " + ", ".join(sorted(ENTRY_KEYS)))
    bad = sorted(key for key, pred in ENTRY_FIELDS.items() if not pred(obj[key]))
    if bad:
        return ("BAD_ENTRY", "invalid entry fields: " + ", ".join(bad))
    return None


class Verifier:
    """Incremental ledger checker. Feed complete lines (without the newline) in order."""

    def __init__(self, card_hasher: CardHasher | None = None) -> None:
        self.card_hasher = card_hasher
        self.index = 0
        self.prev_hash: str | None = ZERO_HASH
        self.prev_ts: str | None = None
        self.entries: dict[int, Entry] = {}
        self.protocols: dict[str, dict[str, Any]] = {}
        self.frozen_ids: dict[tuple[str, str], int] = {}

    @property
    def tip_hash(self) -> str:
        return self.prev_hash or ZERO_HASH

    def feed(self, line: bytes, *, last: bool = False) -> list[Violation]:
        index = self.index
        self.index += 1
        found: list[Violation] = []
        add: Add = partial(_add, found, index)
        expected_prev = self.prev_hash
        entry = self._read(line, last, add)
        if entry is None:
            return found
        self._chain(index, line, entry, expected_prev, add)
        handler = {
            "freeze": self._freeze,
            "record": self._record,
            "deviation": self._deviation,
            "issue": self._issue,
        }[entry["type"]]
        if handler(index, entry["body"], add):
            self.entries[index] = entry
        self.prev_ts = entry["ts"]
        return found

    def _read(self, line: bytes, last: bool, add: Add) -> Entry | None:
        self.prev_hash = None
        if len(line) > MAX_ENTRY_BYTES:
            add("ENTRY_TOO_LARGE", f"entry is {len(line)} bytes, limit {MAX_ENTRY_BYTES}")
            return None
        try:
            obj = decode(line)
        except CanonError as exc:
            code = "TOO_DEEP" if exc.code == "TOO_DEEP" else ("TRUNCATED_TAIL" if last else "BAD_ENTRY")
            add(code, f"line does not parse: {exc.code}: {exc.message}")
            return None
        self.prev_hash = _tip_of(obj)
        problem = _structure(obj)
        if problem is not None:
            add(*problem)
            return None
        entry: Entry = obj
        return entry

    def _chain(self, index: int, line: bytes, entry: Entry, expected_prev: str | None, add: Add) -> None:
        if entry["seq"] != index:
            add("BAD_SEQ", f"seq is {entry['seq']}, expected {index}")
        if expected_prev is not None and entry["prev"] != expected_prev:
            add("BAD_PREV", "prev does not equal the previous entry hash")
        if entry_hash(entry) != entry["hash"]:
            add("BAD_HASH", "hash does not match the recomputed value")
        if encode(entry) != line:
            add("NOT_CANONICAL", "line is not the exact canonical form")
        if self.prev_ts is not None and entry["ts"] < self.prev_ts:
            add("TS_REGRESSION", f"ts {entry['ts']} is earlier than {self.prev_ts}")

    def _shape(self, body: Entry, required: Mapping[str, Pred], optional: Mapping[str, Pred], add: Add) -> bool:
        problems = shape_problems(body, required, optional)
        for code, message in problems:
            add(code, message)
        return not problems

    def _known_protocol(self, body: Entry, add: Add) -> None:
        if body["protocol_sha256"] not in self.protocols:
            add("UNKNOWN_PROTOCOL", "protocol_sha256 was not frozen at an earlier seq")

    def _freeze(self, index: int, body: Entry, add: Add) -> bool:
        if not self._shape(body, FREEZE_FIELDS, {}, add):
            return False
        protocol = body["protocol"]
        if sha256_hex(protocol) != body["protocol_sha256"]:
            add("BAD_HASH", "protocol_sha256 does not match protocol")
        if protocol.get("protocol_id") != body["protocol_id"] or protocol.get("version") != body["version"]:
            add("BAD_ENTRY", "protocol_id and version must match the frozen protocol")
        old = self.protocols.get(body["supersedes"] or "")
        if body["supersedes"] is not None and (old is None or old["protocol_id"] != body["protocol_id"]):
            add("UNKNOWN_PROTOCOL", "supersedes does not name an earlier freeze of the same protocol_id")
        key = (body["protocol_id"], body["version"])
        if key in self.frozen_ids or body["protocol_sha256"] in self.protocols:
            add("DUPLICATE_FREEZE", f"{key[0]} version {key[1]} is already frozen")
        self.frozen_ids.setdefault(key, index)
        self.protocols.setdefault(
            body["protocol_sha256"],
            {"seq": index, "protocol_id": key[0], "version": key[1], "protocol": protocol},
        )
        return True

    def _record(self, index: int, body: Entry, add: Add) -> bool:
        if not self._shape(body, RECORD_FIELDS, RECORD_OPTIONAL, add):
            return False
        status = body["status"]
        if not (isinstance(status, str) and status in RESULT_STATUSES):
            add("BAD_STATUS", f"status is not in the closed set: {status!r}")
        else:
            needed = [_BLOCKING[status]] if status in _BLOCKING and _BLOCKING[status] not in body else []
            if status in _NEEDS_SOURCES and not body["sources"]:
                needed.append("sources")
            if needed:
                add("MISSING_FIELD", f"status {status} requires: " + ", ".join(needed))
        self._known_protocol(body, add)
        for ref in body["deviations"]:
            target = self.entries.get(ref)
            if target is None or target["type"] != "deviation":
                add("DANGLING_REF", f"deviations entry {ref} is not an earlier deviation")
            elif target["body"]["protocol_sha256"] != body["protocol_sha256"]:
                add("DANGLING_REF", f"deviation {ref} belongs to another protocol")
        return True

    def _deviation(self, index: int, body: Entry, add: Add) -> bool:
        if not self._shape(body, DEVIATION_FIELDS, {}, add):
            return False
        self._known_protocol(body, add)
        return True

    def _issue(self, index: int, body: Entry, add: Add) -> bool:
        if not self._shape(body, ISSUE_FIELDS, {}, add):
            return False
        target = self.entries.get(body["record_seq"])
        if target is None or target["type"] != "record":
            add("DANGLING_REF", f"record_seq {body['record_seq']} is not an earlier record")
        elif self.card_hasher is not None:
            self._check_card(body, add)
        return True

    def _check_card(self, body: Entry, add: Add) -> None:
        assert self.card_hasher is not None
        try:
            expected = self.card_hasher(self, body["record_seq"])
        except ProtocolithError as exc:
            add("BAD_CARD", f"card cannot be rebuilt: {exc.code}: {exc.message}")
            return
        if expected != body["card_sha256"]:
            add("BAD_CARD", "card_sha256 does not match the card rebuilt from the record")


def _add(found: list[Violation], index: int, code: str, message: str) -> None:
    found.append(Violation(code, index, message))


def scan(data: bytes, card_hasher: CardHasher | None = None) -> tuple[Verdict, Verifier]:
    """Verify a whole ledger given as bytes."""
    verifier = Verifier(card_hasher)
    lines = data.split(b"\n")
    tail = lines.pop()
    violations: list[Violation] = []
    for number, line in enumerate(lines):
        violations.extend(verifier.feed(line, last=number == len(lines) - 1 and not tail))
    if tail:
        violations.append(Violation("TRUNCATED_TAIL", len(lines), "last line is not terminated by a newline"))
    count = len(lines)
    head_hash = verifier.prev_hash if count else None
    verdict = Verdict(not violations, count, count - 1 if head_hash else None, head_hash, violations)
    return verdict, verifier
