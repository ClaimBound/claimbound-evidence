# SPDX-License-Identifier: Apache-2.0
"""The six operations: freeze, record, deviation, verify, issue, log/head, plus repair."""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .canonical import sha256_hex
from .clock import Clock, now_utc
from .errors import InputError, VerificationFailed, io_guard
from .issue import build_card, card_hash, write_card_files
from .ledger import CARD_FORMAT, Entry, make_entry, serialize
from .rules import Verdict, Verifier, scan
from .store import Store

StoreLike = Store | str | os.PathLike[str]


def _as_store(store: StoreLike) -> Store:
    return store if isinstance(store, Store) else Store(store)


@contextmanager
def _session(store: StoreLike, *, write: bool) -> Iterator[Store]:
    real = _as_store(store)
    with io_guard(), real.locked(write=write):
        yield real


def _load(store: Store, *, missing_ok: bool) -> Verifier:
    verdict, verifier = scan(store.read(missing_ok=missing_ok), card_hash)
    if not verdict.ok:
        raise VerificationFailed(verdict.violations)
    return verifier


def _stage(verifier: Verifier, type: str, body: Mapping[str, Any], clock: Clock | None) -> tuple[Entry, bytes]:
    """Build the next entry and check it against every rule before anything is written."""
    entry = make_entry(seq=verifier.index, prev=verifier.tip_hash, ts=now_utc(clock), type=type, body=body)
    line = serialize(entry)
    found = verifier.feed(line[:-1])
    if found:
        raise InputError(found[0].code, "; ".join(v.message for v in found), found)
    return entry, line


def _append(store: Store, type: str, body: Mapping[str, Any], clock: Clock | None) -> Entry:
    entry, line = _stage(_load(store, missing_ok=True), type, body, clock)
    store.append_line(line)
    return entry


def freeze(store: StoreLike, protocol: Any, *, supersedes: str | None = None, clock: Clock | None = None) -> Entry:
    """Freeze a protocol (an object with ``protocol_id`` and ``version``)."""
    if not isinstance(protocol, dict):
        raise InputError("BAD_ENTRY", "protocol must be an object")
    body = {
        "protocol_id": protocol.get("protocol_id", ""),
        "protocol": protocol,
        "protocol_sha256": sha256_hex(protocol),
        "supersedes": supersedes,
        "version": protocol.get("version", ""),
    }
    with _session(store, write=True) as real:
        return _append(real, "freeze", body, clock)


def record(store: StoreLike, body: Any, *, clock: Clock | None = None) -> Entry:
    return _typed(store, "record", body, clock)


def deviation(store: StoreLike, body: Any, *, clock: Clock | None = None) -> Entry:
    return _typed(store, "deviation", body, clock)


def _typed(store: StoreLike, type: str, body: Any, clock: Clock | None) -> Entry:
    if not isinstance(body, dict):
        raise InputError("BAD_ENTRY", f"{type} body must be an object")
    with _session(store, write=True) as real:
        return _append(real, type, body, clock)


def verify(store: StoreLike) -> Verdict:
    with _session(store, write=False) as real:
        return scan(real.read(missing_ok=False), card_hash)[0]


def entries(store: StoreLike) -> list[Entry]:
    with _session(store, write=False) as real:
        verifier = _load(real, missing_ok=False)
    return [verifier.entries[i] for i in range(verifier.index)]


def head(store: StoreLike) -> dict[str, Any]:
    """The last entry hash and seq, to be published or anchored elsewhere."""
    with _session(store, write=False) as real:
        verifier = _load(real, missing_ok=False)
    empty = verifier.index == 0
    return {
        "count": verifier.index,
        "hash": None if empty else verifier.tip_hash,
        "seq": None if empty else verifier.index - 1,
    }


def issue(store: StoreLike, seq: int, *, out: str | os.PathLike[str] | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Render the card of record ``seq`` to JSON and SVG and record an ``issue`` entry."""
    if type(seq) is not int:
        raise InputError("BAD_ENTRY", "seq must be an integer")
    with _session(store, write=True) as real:
        verifier = _load(real, missing_ok=False)
        target = verifier.entries.get(seq)
        if target is None or target["type"] != "record":
            raise InputError("DANGLING_REF", f"seq {seq} is not a record")
        card = build_card(verifier, seq)
        body = {"card_sha256": sha256_hex(card), "format": CARD_FORMAT, "record_seq": seq}
        entry, line = _stage(verifier, "issue", body, clock)
        json_path, svg_path = write_card_files(card, Path(out) if out is not None else real.cards_dir)
        real.append_line(line)
    return {"card": card, "entry": entry, "json_path": str(json_path), "svg_path": str(svg_path)}


def repair_truncate_partial_tail(store: StoreLike) -> int:
    """Remove the unterminated last line. Returns the number of bytes removed."""
    with _session(store, write=True) as real:
        data = real.read(missing_ok=False)
        keep = data.rfind(b"\n") + 1
        if keep == len(data):
            raise InputError("NO_PARTIAL_TAIL", "the ledger has no partial last line")
        verdict, _ = scan(data[:keep], card_hash)
        if not verdict.ok:
            raise VerificationFailed(verdict.violations)
        real.truncate(keep)
        return len(data) - keep
