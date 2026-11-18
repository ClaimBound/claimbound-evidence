# SPDX-License-Identifier: Apache-2.0
"""Build, validate and write the evidence card for a record."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from protocolith.card_svg_render import render_svg
from protocolith.evidence_card import validate_evidence_card

from .canonical import encode, sha256_hex
from .errors import InputError
from .rules import Verifier

_MISSING_RE = re.compile(r"^missing (?:required |forecast |public claim )?field: (\w+)$")
_MUST_INCLUDE_RE = re.compile(r"must include (\w+)$")
# Characters that are not allowed in XML 1.0 documents (listed as code points, not as a regular expression range).
_XML_INVALID = frozenset(map(chr, (*range(0x00, 0x09), 0x0B, 0x0C, *range(0x0E, 0x20), 0xFFFE, 0xFFFF)))


def _xml_safe(text: str) -> str:
    """Replace the characters XML 1.0 cannot carry with U+FFFD."""
    return "".join("\ufffd" if ch in _XML_INVALID else ch for ch in text)


def _missing_names(violations: list[str]) -> list[str]:
    names: set[str] = set()
    for text in violations:
        found = _MISSING_RE.match(text) or _MUST_INCLUDE_RE.search(text)
        if found:
            names.add(found.group(1))
    return sorted(names)


def build_card(verifier: Verifier, record_seq: int) -> dict[str, Any]:
    """Derive the card for the record at ``record_seq`` from the ledger state held by ``verifier``."""
    entry = verifier.entries[record_seq]
    body = entry["body"]
    frozen = verifier.protocols.get(body["protocol_sha256"])
    if frozen is None:
        raise InputError("UNKNOWN_PROTOCOL", "the record names a protocol that is not frozen")
    day = entry["ts"][:10]
    fixed: dict[str, Any] = {
        "claim_boundary": body["claim_boundary"],
        "created_at": entry["ts"],
        "evidence_id": f"PLITH-{frozen['protocol_id']}-{day}-{record_seq:06d}",
        "ledger_record_seq": record_seq,
        "protocol_id": frozen["protocol_id"],
        "protocol_sha256": body["protocol_sha256"],
        "protocol_version": frozen["version"],
        "raw_payload_committed": False,
        "reproduction_level": body["reproduction_level"],
        "result_status": body["status"],
        "sources": body["sources"],
    }
    for reason in ("block_reason", "drift_reason"):
        if reason in body:
            fixed[reason] = body[reason]
    extra: dict[str, Any] = body.get("card", {})
    conflicts = sorted(key for key in extra if key in fixed and extra[key] != fixed[key])
    if conflicts:
        raise InputError("CARD_CONFLICT", "card fields contradict the record: " + ", ".join(conflicts))
    defaults = {"last_verified_date": day, "record_type": "evidence_result", "registry_sequence": record_seq + 1}
    card = {**defaults, **extra, **fixed}
    try:
        violations = validate_evidence_card(card)
    except Exception as exc:  # the validator was written for trusted input; card metadata is user data
        raise InputError("CARD_INVALID", f"card cannot be validated: {type(exc).__name__}") from None
    if violations:
        names = _missing_names(violations)
        if names:
            raise InputError("MISSING_FIELD", "card is missing fields: " + ", ".join(names))
        raise InputError("CARD_INVALID", "; ".join(violations))
    return card


def card_hash(verifier: Verifier, record_seq: int) -> str:
    return sha256_hex(build_card(verifier, record_seq))


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_card_files(card: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``<evidence_id>.json`` (PCJ-1 bytes) and ``.svg``; refuse to replace a different card."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{card['evidence_id']}.json"
    svg_path = json_path.with_suffix(".svg")
    payload = encode(card)
    if json_path.exists() and json_path.read_bytes() != payload:
        raise InputError("CARD_EXISTS", f"{json_path.name} already exists with different content; use another --out")
    _atomic_write(json_path, payload)
    # Card text is user data and may hold characters XML 1.0 forbids; the JSON card keeps them verbatim.
    _atomic_write(svg_path, _xml_safe(render_svg(json_path)).encode("utf-8"))
    return json_path, svg_path
