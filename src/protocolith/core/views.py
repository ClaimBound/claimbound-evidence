# SPDX-License-Identifier: Apache-2.0
"""Read-only views over a loaded ledger: filtered log, one entry with context, and the summary."""

from __future__ import annotations

from typing import Any

from .errors import InputError
from .ledger import ENTRY_TYPES, RESULT_STATUSES, Entry
from .rules import Verdict, Verifier


def _protocol_sha(verifier: Verifier, entry: Entry) -> str | None:
    """The protocol hash an entry refers to (an issue entry refers to the protocol of its record)."""
    body = entry["body"]
    if entry["type"] == "issue":
        target = verifier.entries.get(body["record_seq"])
        return None if target is None else _protocol_sha(verifier, target)
    return str(body["protocol_sha256"])


def protocol_of(verifier: Verifier, entry: Entry) -> str | None:
    """The ``protocol_id`` an entry belongs to, or None when its protocol was never frozen."""
    if entry["type"] == "freeze":
        return str(entry["body"]["protocol_id"])
    frozen = verifier.protocols.get(_protocol_sha(verifier, entry) or "")
    return None if frozen is None else str(frozen["protocol_id"])


def _ordered(verifier: Verifier) -> list[Entry]:
    return [verifier.entries[i] for i in sorted(verifier.entries)]


def _require_protocol(verifier: Verifier, protocol: str | None) -> None:
    if protocol is not None and all(p["protocol_id"] != protocol for p in verifier.protocols.values()):
        raise InputError("UNKNOWN_PROTOCOL", f"no protocol {protocol!r} is frozen in this ledger")


def select(
    verifier: Verifier,
    *,
    protocol: str | None = None,
    entry_type: str | None = None,
    status: str | None = None,
    tail: int | None = None,
) -> list[Entry]:
    """Entries matching every given filter, in ledger order; ``tail`` keeps the last N matches."""
    if entry_type is not None and entry_type not in ENTRY_TYPES:
        raise InputError("BAD_ENTRY", f"type must be one of: {', '.join(ENTRY_TYPES)}")
    if status is not None and status not in RESULT_STATUSES:
        raise InputError("BAD_STATUS", f"status must be one of: {', '.join(sorted(RESULT_STATUSES))}")
    if tail is not None and not (type(tail) is int and tail >= 1):
        raise InputError("BAD_ENTRY", "tail must be an integer of at least 1")
    _require_protocol(verifier, protocol)
    found = [
        entry
        for entry in _ordered(verifier)
        if (entry_type is None or entry["type"] == entry_type)
        and (status is None or entry["body"].get("status") == status)
        and (protocol is None or protocol_of(verifier, entry) == protocol)
    ]
    return found if tail is None else found[-tail:]


def show(verifier: Verifier, seq: int) -> dict[str, Any]:
    """One entry, the protocol it belongs to, the entries it points at and the entries that point at it."""
    if type(seq) is not int or seq not in verifier.entries:
        raise InputError("DANGLING_REF", f"there is no valid entry at seq {seq!r}")
    entry = verifier.entries[seq]
    body = entry["body"]
    sha = _protocol_sha(verifier, entry) or ""
    frozen = verifier.protocols.get(sha)
    context = None
    if frozen is not None:
        context = {
            "freeze_seq": frozen["seq"],
            "protocol_id": frozen["protocol_id"],
            "protocol_sha256": sha,
            "version": frozen["version"],
        }
    points_at = list(body["deviations"]) if entry["type"] == "record" else []
    if entry["type"] == "issue":
        points_at = [body["record_seq"]]
    pointed_by = [
        other["seq"]
        for other in _ordered(verifier)
        if (other["type"] == "issue" and other["body"]["record_seq"] == seq)
        or (other["type"] == "record" and seq in other["body"]["deviations"])
    ]
    return {"entry": entry, "points_at": points_at, "pointed_by": pointed_by, "protocol": context}


def summarize(verdict: Verdict, verifier: Verifier, protocol: str | None = None) -> dict[str, Any]:
    """Verdict, head, counts and a per-protocol table. Computed from the entries that parsed and passed their shape checks."""
    _require_protocol(verifier, protocol)
    by_type = dict.fromkeys(ENTRY_TYPES, 0)
    by_status: dict[str, int] = {}
    table: dict[str, dict[str, Any]] = {}
    for entry in _ordered(verifier):
        pid = protocol_of(verifier, entry)
        if pid is None or (protocol is not None and pid != protocol):
            continue
        body = entry["body"]
        by_type[entry["type"]] += 1
        row = table.setdefault(
            pid,
            {
                "cards": 0,
                "deviations": 0,
                "latest_status": None,
                "latest_version": None,
                "protocol_id": pid,
                "records": 0,
                "versions": [],
            },
        )
        if entry["type"] == "freeze":
            row["versions"].append(body["version"])
            row["latest_version"] = body["version"]
        elif entry["type"] == "record":
            row["records"] += 1
            row["latest_status"] = body["status"]
            by_status[body["status"]] = by_status.get(body["status"], 0) + 1
        elif entry["type"] == "deviation":
            row["deviations"] += 1
        else:
            row["cards"] += 1
    problems = [{"code": v.code, "message": v.message, "seq": v.seq} for v in verdict.violations]
    return {
        "entries_by_type": by_type,
        "head": {"count": verdict.count, "hash": verdict.head_hash, "seq": verdict.head_seq},
        "ok": verdict.ok,
        "problems": problems,
        "protocols": [table[pid] for pid in sorted(table)],
        "records_by_status": dict(sorted(by_status.items())),
    }
