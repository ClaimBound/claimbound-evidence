# SPDX-License-Identifier: Apache-2.0
"""Card metadata is user data: whatever it holds, issue must succeed or raise a documented InputError."""

from __future__ import annotations

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from hardening_support import CARD, PROTOCOL, PROTOCOL_SHA, clock_at, record_body
from hypothesis import example, given
from hypothesis import strategies as st

from protocolith.core import InputError, Store, decode, encode, freeze, issue, record, verify
from protocolith.core.canonical import CanonError

JUNK = st.recursive(
    st.one_of(
        st.none(), st.booleans(), st.integers(-3, 3), st.integers(-(2**53 - 1), 2**53 - 1),
        st.text(max_size=12), st.sampled_from(["<script>&\"'", "\x00", "‮", "a" * 300, "", " "]),
    ),
    lambda inner: st.one_of(st.lists(inner, max_size=3), st.dictionaries(st.text(max_size=5), inner, max_size=3)),
    max_leaves=5,
)  # fmt: skip


@given(st.sampled_from(sorted(CARD)), JUNK, st.booleans())
@example("known_limitations", ["<b>x</b>"], False)
@example("operator", "<&>\"'", False)
@example("verification_count", True, False)
def test_issue_with_one_hostile_card_field(field: str, junk: Any, drop: bool) -> None:
    card = dict(CARD)
    if drop:
        card.pop(field)
    else:
        card[field] = junk
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "s")
        freeze(store, PROTOCOL, clock=clock_at(0))
        try:
            record(store, record_body(card=card), clock=clock_at(1))
            result = issue(store, 1, clock=clock_at(2))
        except InputError:
            return
        assert verify(store).ok
        svg = Path(result["svg_path"]).read_text(encoding="utf-8")
        ET.fromstring(svg)  # the rendered SVG is always well-formed XML
        assert decode(Path(result["json_path"]).read_bytes()) == result["card"]
        assert encode(result["card"]) == Path(result["json_path"]).read_bytes()


@given(st.dictionaries(st.sampled_from(sorted(CARD) + ["card", "sources", "claim_boundary", "evidence_id"]), JUNK, max_size=6))
def test_issue_with_arbitrary_card_object(card: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "s")
        freeze(store, PROTOCOL, clock=clock_at(0))
        try:
            record(store, record_body(card=card), clock=clock_at(1))
            issue(store, 1, clock=clock_at(2))
        except (InputError, CanonError):
            return
        assert verify(store).ok


def test_protocol_sha_constant_is_consistent() -> None:
    assert len(PROTOCOL_SHA) == 64
