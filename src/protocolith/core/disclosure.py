# SPDX-License-Identifier: Apache-2.0
"""Selective disclosure: publish a view of a ledger in which each entry is shown in full, as a summary, or hidden.

A *policy* decides the level of every entry. The *disclosure* is a canonical JSON Lines file:

- line 0, the manifest: kind, format version, number of entries, the head, and how many entries have each level;
- then one line per ledger entry, in order, shaped by its level:
  ``full`` carries the whole entry, ``summary`` carries ``seq``, ``prev``, ``hash``, ``type``, ``ts`` and a few chosen
  fields, ``hidden`` carries only ``seq``, ``prev`` and ``hash``.

Every line keeps the entry's own hash and the hash of the entry before it, so the chain stays linked and the head covers
the hidden entries too. A reader therefore sees how many entries exist and that none was dropped, but nothing of the content
that was hidden. The owner can reveal a hidden or summarised entry later: anyone checks that the revealed entry has exactly
the published hash. Nothing here changes the ledger or its rules R1 to R11.

Limits, stated plainly: a hidden hash does not reveal the content, but a reader who can guess the whole entry (for example a
short, predictable body) can confirm the guess; a summary is a statement of the owner that is checked only when the entry is
revealed; and publishing nothing about an entry does not hide that it exists.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .anchor import check_anchor_hashes
from .canonical import CanonError, decode, encode
from .errors import InputError, VerificationFailed, Violation, io_guard
from .issue import card_hash
from .ledger import ENTRY_KEYS, ENTRY_TYPES, ZERO_HASH, Entry, entry_hash, is_hash, is_ts
from .rules import Verifier, scan
from .store import Store
from .views import protocol_of

KIND = "protocolith-disclosure"
FORMAT_VERSION = 1
LEVELS = ("full", "summary", "hidden")
SUMMARY_CHOICES = ("claim_boundary", "outcome", "public_claim_text", "question", "reproduction_level", "run_id", "status")
DEFAULT_SUMMARY = ("status", "reproduction_level", "claim_boundary")
DEFAULT_LEVEL = "hidden"
RULES_LIMIT = 10_000
MAX_NAME = 200
_POLICY_KEYS = frozenset({"default", "rules", "summary_fields", "v"})
RULEKEYS = frozenset({"from_seq", "level", "protocol_id", "seq", "to_seq"})
_MANIFEST_KEYS = frozenset({"counts", "entries", "head_hash", "head_seq", "kind", "v"})
_LINE_KEYS = {
    "full": frozenset({"entry", "level", "seq"}),
    "summary": frozenset({"hash", "level", "prev", "seq", "summary", "ts", "type"}),
    "hidden": frozenset({"hash", "level", "prev", "seq"}),
}
_RANK = {"hidden": 0, "summary": 1, "full": 2}


def _uint(value: object) -> bool:
    return type(value) is int and value >= 0


@dataclass(frozen=True)
class Rule:
    """One policy rule: a level for the entries of a protocol (``ID`` or ``PREFIX*``) or for some sequence numbers."""

    level: str
    protocol: str | None = None
    seqs: frozenset[int] | None = None
    span: tuple[int, int] | None = None

    def matches(self, seq: int, protocol: str | None) -> bool:
        if self.protocol is not None:
            if protocol is None:
                return False
            if self.protocol.endswith("*"):
                return protocol.startswith(self.protocol[:-1])
            return protocol == self.protocol
        if self.seqs is not None:
            return seq in self.seqs
        assert self.span is not None
        return self.span[0] <= seq <= self.span[1]


@dataclass(frozen=True)
class Policy:
    """Which entries are shown how. The first matching rule wins; ``default`` applies when none matches."""

    default: str = DEFAULT_LEVEL
    rules: tuple[Rule, ...] = ()
    summary_fields: tuple[str, ...] = DEFAULT_SUMMARY

    def level_for(self, seq: int, protocol: str | None) -> str:
        for rule in self.rules:
            if rule.matches(seq, protocol):
                return rule.level
        return self.default


def _bad(message: str) -> InputError:
    return InputError("BAD_POLICY", message)


def _level(value: object, where: str) -> str:
    if value not in LEVELS:
        raise _bad(f"{where}: level must be one of {', '.join(LEVELS)}")
    return str(value)


def _protocol_selector(value: object, where: str) -> str:
    if not (isinstance(value, str) and value and len(value) <= MAX_NAME) or "*" in value[:-1]:
        raise _bad(f"{where}: protocol_id must be a non-empty string; a * is allowed only as the last character")
    return value


def _seq_list(value: object, where: str) -> frozenset[int]:
    items = value if isinstance(value, list) else [value]
    if not items or not all(_uint(item) for item in items):
        raise _bad(f"{where}: seq must be a non-negative integer or a non-empty list of them")
    return frozenset(items)


def _parse_rule(raw: object, index: int) -> Rule:
    where = f"rules[{index}]"
    if not isinstance(raw, dict):
        raise _bad(f"{where}: must be an object")
    unknown = sorted(set(raw) - RULEKEYS)
    if unknown:
        raise _bad(f"{where}: unknown keys {', '.join(unknown)}")
    if "level" not in raw:
        raise _bad(f"{where}: level is required")
    level = _level(raw["level"], where)
    chosen = [k for k in ("protocol_id", "seq") if k in raw] + (["span"] if ("from_seq" in raw or "to_seq" in raw) else [])
    if len(chosen) != 1:
        raise _bad(f"{where}: give exactly one of protocol_id, seq, or from_seq with to_seq")
    if chosen[0] == "protocol_id":
        return Rule(level, protocol=_protocol_selector(raw["protocol_id"], where))
    if chosen[0] == "seq":
        return Rule(level, seqs=_seq_list(raw["seq"], where))
    low, high = raw.get("from_seq"), raw.get("to_seq")
    if not (isinstance(low, int) and isinstance(high, int) and _uint(low) and _uint(high) and low <= high):
        raise _bad(f"{where}: from_seq and to_seq must both be non-negative integers with from_seq <= to_seq")
    return Rule(level, span=(low, high))


def parse_policy(doc: object) -> Policy:
    """Validate a policy object (see ``schema_for("policy")``); BAD_POLICY on any problem."""
    if not isinstance(doc, dict):
        raise _bad("a policy must be a JSON object")
    unknown = sorted(set(doc) - _POLICY_KEYS)
    if unknown:
        raise _bad("unknown keys: " + ", ".join(unknown))
    if doc.get("v", FORMAT_VERSION) != FORMAT_VERSION:
        raise _bad(f"v must be {FORMAT_VERSION}")
    default = _level(doc.get("default", DEFAULT_LEVEL), "default")
    raw_rules = doc.get("rules", [])
    if not isinstance(raw_rules, list) or len(raw_rules) > RULES_LIMIT:
        raise _bad(f"rules must be a list of at most {RULES_LIMIT} objects")
    rules = tuple(_parse_rule(raw, index) for index, raw in enumerate(raw_rules))
    fields = doc.get("summary_fields", list(DEFAULT_SUMMARY))
    if not (isinstance(fields, list) and all(isinstance(f, str) for f in fields) and len(set(fields)) == len(fields)):
        raise _bad("summary_fields must be a list of distinct strings")
    bad = sorted(set(fields) - set(SUMMARY_CHOICES))
    if bad:
        raise _bad(f"summary_fields: unknown {', '.join(bad)}; choose from {', '.join(SUMMARY_CHOICES)}")
    return Policy(default, rules, tuple(fields))


def load_policy(path: str | os.PathLike[str]) -> Policy:
    """Read a policy file (strict JSON, no floats)."""
    with io_guard():
        raw = Path(path).read_bytes()
    try:
        return parse_policy(decode(raw))
    except CanonError as exc:
        raise InputError("BAD_POLICY", f"{path}: {exc.message}") from None


def summarize_entry(entry: Mapping[str, Any], protocol: str | None, fields: Sequence[str]) -> dict[str, Any]:
    """The few facts a ``summary`` line carries. Only what the policy lists is taken from a record or a freeze."""
    body = entry["body"]
    out: dict[str, Any] = {}
    if protocol is not None:
        out["protocol_id"] = protocol
    kind = entry["type"]
    if kind == "freeze":
        out["version"] = body["version"]
        question = body.get("protocol", {}).get("question") if isinstance(body.get("protocol"), dict) else None
        if "question" in fields and question is not None:
            out["question"] = question
    elif kind == "record":
        card = body.get("card") if isinstance(body.get("card"), dict) else {}
        found = {
            "claim_boundary": body.get("claim_boundary"),
            "outcome": body.get("outcome"),
            "public_claim_text": card.get("public_claim_text"),
            "reproduction_level": body.get("reproduction_level"),
            "run_id": body.get("run_id"),
            "status": body.get("status"),
        }
        out.update({key: value for key, value in found.items() if key in fields and value is not None})
    elif kind == "issue":
        out["record_seq"] = body["record_seq"]
    return out


@dataclass
class Disclosure:
    """The bytes of a disclosure file plus what a caller reports."""

    data: bytes
    counts: dict[str, int]
    head_seq: int | None
    head_hash: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bytes": len(self.data),
            "counts": self.counts,
            "entries": sum(self.counts.values()),
            "head": {"hash": self.head_hash, "seq": self.head_seq},
            "warnings": self.warnings,
        }


def levels_of(verifier: Verifier, policy: Policy) -> list[str]:
    """The level of every entry, in order."""
    return [
        policy.level_for(seq, protocol_of(verifier, verifier.entries[seq])) for seq in range(verifier.index)
    ]


def _warnings(verifier: Verifier, levels: Sequence[str]) -> list[str]:
    """A record that is shown more than the freeze of its protocol cannot be read in context."""
    weakest: dict[str, int] = {}
    for seq, level in enumerate(levels):
        entry = verifier.entries[seq]
        if entry["type"] == "freeze":
            weakest[entry["body"]["protocol_id"]] = _RANK[level]
    found = []
    for seq, level in enumerate(levels):
        entry = verifier.entries[seq]
        protocol = protocol_of(verifier, entry)
        if entry["type"] == "record" and protocol in weakest and _RANK[level] > weakest[protocol]:
            found.append(f"seq {seq}: the record is shown more than the freeze of protocol {protocol}")
    return found


def disclose_verifier(verifier: Verifier, policy: Policy) -> Disclosure:
    levels = levels_of(verifier, policy)
    counts = {name: levels.count(name) for name in LEVELS}
    count = verifier.index
    head_hash = verifier.prev_hash if count else None
    lines: list[dict[str, Any]] = [
        {
            "counts": counts,
            "entries": count,
            "head_hash": head_hash,
            "head_seq": count - 1 if count else None,
            "kind": KIND,
            "v": FORMAT_VERSION,
        }
    ]
    for seq, level in enumerate(levels):
        entry: Entry = verifier.entries[seq]
        if level == "full":
            lines.append({"entry": entry, "level": "full", "seq": seq})
        elif level == "summary":
            summary = summarize_entry(entry, protocol_of(verifier, entry), policy.summary_fields)
            lines.append(
                {"hash": entry["hash"], "level": "summary", "prev": entry["prev"], "seq": seq, "summary": summary,
                 "ts": entry["ts"], "type": entry["type"]}
            )
        else:
            lines.append({"hash": entry["hash"], "level": "hidden", "prev": entry["prev"], "seq": seq})
    data = b"".join(encode(line) + b"\n" for line in lines)
    return Disclosure(data, counts, count - 1 if count else None, head_hash, _warnings(verifier, levels))


def build_disclosure(store: Store | str | os.PathLike[str], policy: Policy) -> Disclosure:
    """Verify the ledger, then build the disclosure the policy asks for. A ledger that fails verification is never disclosed."""
    real = store if isinstance(store, Store) else Store(store)
    with io_guard(), real.locked(write=False):
        verdict, verifier = scan(real.read(missing_ok=False), card_hash)
    if not verdict.ok:
        raise VerificationFailed(verdict.violations)
    return disclose_verifier(verifier, policy)


@dataclass
class DisclosureReport:
    ok: bool
    entries: int
    counts: dict[str, int]
    head_seq: int | None
    head_hash: str | None
    anchors: int | None
    violations: list[Violation]

    @property
    def codes(self) -> list[str]:
        return sorted({v.code for v in self.violations})

    def to_dict(self) -> dict[str, Any]:
        found: dict[str, Any] = {
            "codes": self.codes,
            "counts": self.counts,
            "entries": self.entries,
            "head": {"hash": self.head_hash, "seq": self.head_seq},
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
        }
        if self.anchors is not None:
            found["anchors"] = self.anchors
        return found


def _decode_lines(data: bytes) -> tuple[list[dict[str, Any]], list[Violation]]:
    """Parse every line as canonical JSON; a line that fails is reported and skipped."""
    found: list[Violation] = []
    objects: list[dict[str, Any]] = []
    pieces = data.split(b"\n")
    tail = pieces.pop()
    if tail:
        found.append(Violation("BAD_DISCLOSURE", len(pieces), "the last line is not terminated by a newline"))
    for number, piece in enumerate(pieces):
        try:
            obj = decode(piece)
        except CanonError as exc:
            found.append(Violation("BAD_DISCLOSURE", number, f"not valid JSON: {exc.message}"))
            objects.append({})
            continue
        if not isinstance(obj, dict):
            found.append(Violation("BAD_DISCLOSURE", number, "a line must be a JSON object"))
        elif encode(obj) != piece:
            found.append(Violation("BAD_DISCLOSURE", number, "the line is not in canonical form"))
        else:
            objects.append(obj)
            continue
        objects.append({})
    return objects, found


def _check_line(obj: dict[str, Any], seq: int, expected_prev: str) -> tuple[list[Violation], str | None]:
    """Problems of one entry line and its hash when readable."""
    level = obj.get("level")
    if level not in _LINE_KEYS or set(obj) != _LINE_KEYS[level]:
        return [Violation("BAD_DISCLOSURE", seq, "unknown level or unexpected keys")], None
    if obj["seq"] != seq or type(obj["seq"]) is not int:
        return [Violation("BAD_DISCLOSURE", seq, f"seq must be {seq}")], None
    found: list[Violation] = []
    if level == "full":
        entry = obj["entry"]
        if not (isinstance(entry, dict) and set(entry) == ENTRY_KEYS and is_hash(entry["hash"]) and is_hash(entry["prev"])):
            return [Violation("BAD_DISCLOSURE", seq, "a full line must carry a complete entry")], None
        if entry["seq"] != seq:
            found.append(Violation("BAD_DISCLOSURE", seq, "the entry has another seq"))
        if entry_hash(entry) != entry["hash"]:
            found.append(Violation("DISCLOSURE_HASH", seq, "the entry does not hash to its stated hash"))
        digest, prev = entry["hash"], entry["prev"]
    else:
        digest, prev = obj["hash"], obj["prev"]
        if not (is_hash(digest) and is_hash(prev)):
            return [Violation("BAD_DISCLOSURE", seq, "hash and prev must be 64 lowercase hex characters")], None
        if level == "summary" and not (
            obj["type"] in ENTRY_TYPES and is_ts(obj["ts"]) and isinstance(obj["summary"], dict)
        ):
            found.append(Violation("BAD_DISCLOSURE", seq, "a summary needs a known type, a time-stamp and an object"))
    if prev != expected_prev:
        found.append(Violation("DISCLOSURE_CHAIN", seq, "prev is not the hash of the entry before"))
    return found, digest


def _check_manifest(manifest: dict[str, Any], count: int, counts: dict[str, int], tip: str | None) -> list[Violation]:
    if set(manifest) != _MANIFEST_KEYS or manifest["kind"] != KIND or manifest["v"] != FORMAT_VERSION:
        return [Violation("BAD_DISCLOSURE", 0, "line 0 is not a disclosure manifest of this version")]
    found: list[Violation] = []
    if manifest["entries"] != count:
        found.append(Violation("BAD_DISCLOSURE", 0, f"the manifest says {manifest['entries']} entries, the file has {count}"))
    if manifest["counts"] != counts:
        found.append(Violation("BAD_DISCLOSURE", 0, "the manifest counts differ from the lines"))
    if manifest["head_hash"] != tip or manifest["head_seq"] != (count - 1 if count else None):
        found.append(Violation("BAD_DISCLOSURE", 0, "the manifest head differs from the last line"))
    return found


def verify_disclosure(data: bytes, anchors_dir: str | os.PathLike[str] | None = None) -> DisclosureReport:
    """Check a disclosure file: structure, hash chain, the hash of every full entry, and optionally the anchors.

    With ``anchors_dir`` every anchor statement there is compared with the entry hash at its position: ANCHOR_MISMATCH
    (the history was replaced) or ANCHOR_AHEAD (entries were removed). Hidden entries are covered through their hashes.
    """
    objects, violations = _decode_lines(data)
    body = objects[1:]
    manifest = objects[0] if objects else {}
    expected, hashes = ZERO_HASH, {}
    counts = {name: 0 for name in LEVELS}
    for seq, obj in enumerate(body):
        if not obj:
            continue
        found, digest = _check_line(obj, seq, expected)
        violations.extend(found)
        if digest is None:
            break
        counts[obj["level"]] += 1
        hashes[seq] = expected = digest
    count = len(body)
    if not objects:
        violations.append(Violation("BAD_DISCLOSURE", 0, "the file is empty"))
    elif not violations:
        violations.extend(_check_manifest(manifest, count, counts, expected if count else None))
    checked = None
    if anchors_dir is not None:
        report = check_anchor_hashes(Path(anchors_dir), hashes, count)
        violations.extend(report.violations)
        checked = report.count
    head = (count - 1, expected) if count else (None, None)
    return DisclosureReport(not violations, count, counts, head[0], head[1], checked, violations)


def _mismatch(seq: object, reason: str) -> dict[str, Any]:
    return {"level": None, "matches": False, "reason": reason, "seq": seq}


def verify_reveal(disclosure: bytes, entry: object) -> dict[str, Any]:
    """Check that a revealed ledger entry is exactly the one a verified disclosure committed to.

    Returns ``{"seq", "level", "matches", "reason"}``; ``matches`` is False, with a reason, when the entry is not the
    published one. BAD_DISCLOSURE is raised when the disclosure itself does not verify.
    """
    report = verify_disclosure(disclosure)
    if not report.ok:
        raise InputError("BAD_DISCLOSURE", "the disclosure does not verify: " + ", ".join(report.codes), report.violations)
    if not (isinstance(entry, dict) and set(entry) == ENTRY_KEYS and is_hash(entry.get("hash"))):
        return _mismatch(None, "the revealed value is not a complete ledger entry")
    seq = entry["seq"]
    if entry_hash(entry) != entry["hash"]:
        return _mismatch(seq, "the revealed entry does not hash to its own hash")
    lines, _ = _decode_lines(disclosure)
    if not (type(seq) is int and 0 <= seq < len(lines) - 1):
        return _mismatch(seq, f"the disclosure has no entry {seq}")
    line = lines[seq + 1]
    published = line["entry"] if line["level"] == "full" else line
    if entry["hash"] != published["hash"] or entry["prev"] != published["prev"]:
        return _mismatch(seq, f"entry {seq} is not the one the disclosure committed to")
    if line["level"] == "summary":
        protocol = entry["body"].get("protocol_id") if entry["type"] == "freeze" else None
        derived = summarize_entry(entry, protocol, SUMMARY_CHOICES)
        wrong = [k for k, v in line["summary"].items() if k in derived and derived[k] != v]
        if wrong or line["type"] != entry["type"] or line["ts"] != entry["ts"]:
            return _mismatch(seq, f"entry {seq}: the published summary does not match the revealed entry")
    return {"level": line["level"], "matches": True, "reason": None, "seq": seq}
