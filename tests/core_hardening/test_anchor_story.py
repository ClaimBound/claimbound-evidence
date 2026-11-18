# SPDX-License-Identifier: Apache-2.0
"""The central story: a ledger rewritten consistently passes verify alone, but not verify with anchors."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from hardening_support import clock_at, deviation_body, protocol, record_body
from hypothesis import assume, given
from hypothesis import strategies as st

from protocolith.core import Store, anchor_head, deviation, freeze, record, verify, verify_anchors
from protocolith.core.ledger import ZERO_HASH, make_entry, serialize

KINDS = st.lists(st.sampled_from(["record", "deviation"]), min_size=2, max_size=6)


def build(store: Store, kinds: list[str]) -> None:
    freeze(store, protocol(), clock=clock_at(0))
    for index, kind in enumerate(kinds, start=1):
        if kind == "record":
            record(store, record_body(run_id=f"run-{index}", card=None), clock=clock_at(index))
        else:
            deviation(store, deviation_body(description=f"d{index}"), clock=clock_at(index))


def rewrite(store: Store, target: int) -> None:
    """Alter the body of entry ``target`` and recompute every prev and hash, so the chain is valid again."""
    prev = ZERO_HASH
    out = b""
    for line in store.ledger_path.read_bytes().splitlines():
        entry: dict[str, Any] = json.loads(line)
        body = entry["body"]
        if entry["seq"] == target:
            body = {**body, "description": "rewritten"} if entry["type"] == "deviation" else {**body, "outcome": {"pass_rate": "0.99"}}  # never the freeze
        rebuilt = make_entry(seq=entry["seq"], prev=prev, ts=entry["ts"], type=entry["type"], body=body)
        out += serialize(rebuilt)
        prev = rebuilt["hash"]
    store.ledger_path.write_bytes(out)


@given(kinds=KINDS, data=st.data())
def test_a_consistent_rewrite_is_caught_only_by_the_anchor(kinds: list[str], data: st.DataObject) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "s")
        build(store, kinds)
        count = len(kinds) + 1
        # anchor at some point; entries may follow it
        anchored_count = data.draw(st.integers(min_value=1, max_value=count))
        original = store.ledger_path.read_bytes()
        store.ledger_path.write_bytes(b"".join(original.splitlines(keepends=True)[:anchored_count]))
        anchor_head(store, clock=clock_at(100))
        store.ledger_path.write_bytes(original)
        assert verify(store, anchors=True).ok

        assume(anchored_count > 1)  # entry 0 is the freeze; rewrite an entry after it
        target = data.draw(st.integers(min_value=1, max_value=anchored_count - 1))
        rewrite(store, target)
        assert verify(store).ok  # the chain is consistent again
        verdict = verify(store, anchors=True)
        assert not verdict.ok and verdict.codes == ["ANCHOR_MISMATCH"]
        assert [v.seq for v in verdict.violations] == [anchored_count - 1]


@given(kinds=KINDS, data=st.data())
def test_truncation_below_the_anchor_is_ahead(kinds: list[str], data: st.DataObject) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "s")
        build(store, kinds)
        count = len(kinds) + 1
        anchor_head(store, clock=clock_at(100))
        keep = data.draw(st.integers(min_value=1, max_value=count - 1))
        lines = store.ledger_path.read_bytes().splitlines(keepends=True)
        store.ledger_path.write_bytes(b"".join(lines[:keep]))
        assert verify(store).ok
        verdict = verify(store, anchors=True)
        assert verdict.codes == ["ANCHOR_AHEAD"] and verify_anchors(store).last_seq is None


def test_rewriting_the_anchored_head_itself_is_caught(tmp_path: Path) -> None:
    store = Store(tmp_path / "s")
    build(store, ["record"])
    anchor_head(store, clock=clock_at(100))
    rewrite(store, 1)
    assert verify(store).ok and verify(store, anchors=True).codes == ["ANCHOR_MISMATCH"]


def test_an_attacker_who_also_edits_the_anchor_file_is_caught_by_the_published_copy(tmp_path: Path) -> None:
    """The local anchor file is evidence only while it is not the attacker's to edit: the statement is what you publish."""
    store = Store(tmp_path / "s")
    build(store, ["record"])
    done = anchor_head(store, clock=clock_at(100), write_head=tmp_path / "published.txt")
    rewrite(store, 1)
    published = json.loads((tmp_path / "published.txt").read_text())
    new_head = verify(store).head_hash
    assert verify(store).ok and published["head_hash"] == done["statement"]["head_hash"] != new_head
