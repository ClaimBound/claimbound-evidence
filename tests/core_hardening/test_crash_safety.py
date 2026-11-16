# SPDX-License-Identifier: Apache-2.0
"""Truncate a valid ledger at every byte offset of its last append: verify and repair must cope."""

from __future__ import annotations

from pathlib import Path

import pytest
from hardening_support import clock_at, deviation_body, protocol, record_body

from protocolith.core import (
    EnvError,
    InputError,
    Store,
    VerificationFailed,
    deviation,
    entries,
    freeze,
    record,
    repair_truncate_partial_tail,
    scan,
    verify,
)
from protocolith.core.issue import card_hash


def make_base(path: Path) -> tuple[Store, bytes]:
    store = Store(path)
    freeze(store, protocol(), clock=clock_at(0))
    deviation(store, deviation_body(), clock=clock_at(1))
    return store, store.ledger_path.read_bytes()


@pytest.mark.parametrize("last", ["deviation", "record_with_unicode"])
def test_truncate_at_every_offset_of_the_last_append(tmp_path: Path, last: str) -> None:
    store, base = make_base(tmp_path / "s")
    if last == "deviation":
        deviation(store, deviation_body(description="café 日本語 \U0001f600"), clock=clock_at(2))
    else:
        record(store, record_body(outcome={"note": "é日\U0001f600" * 20}), clock=clock_at(2))
    full = store.ledger_path.read_bytes()
    assert full.startswith(base) and full.endswith(b"\n")
    appended = len(full) - len(base)
    assert appended > 200
    expected_entries = len(base.splitlines())

    for cut in range(appended + 1):
        data = full[: len(base) + cut]
        store.ledger_path.write_bytes(data)
        verdict = verify(store)
        if cut in (0, appended):
            assert verdict.ok and verdict.count == expected_entries + (cut == appended)
            with pytest.raises(InputError) as nothing:
                repair_truncate_partial_tail(store)
            assert nothing.value.code == "NO_PARTIAL_TAIL"
            assert store.ledger_path.read_bytes() == data
            continue
        assert verdict.codes == ["TRUNCATED_TAIL"], cut
        assert verdict.count == expected_entries
        with pytest.raises(VerificationFailed):
            entries(store)
        # Appending on top of a damaged tail must refuse and leave the file untouched.
        with pytest.raises(VerificationFailed):
            deviation(store, deviation_body(), clock=clock_at(3))
        assert store.ledger_path.read_bytes() == data
        removed = repair_truncate_partial_tail(store)
        assert removed == cut
        assert store.ledger_path.read_bytes() == base  # no complete entry was lost
        assert verify(store).ok
    # and a repaired ledger accepts new entries
    store.ledger_path.write_bytes(base)
    deviation(store, deviation_body(), clock=clock_at(4))
    assert verify(store).count == expected_entries + 1


def test_truncation_inside_the_first_entry_and_empty_file(tmp_path: Path) -> None:
    store = Store(tmp_path / "s")
    freeze(store, protocol(), clock=clock_at(0))
    full = store.ledger_path.read_bytes()
    for cut in range(len(full) + 1):
        store.ledger_path.write_bytes(full[:cut])
        verdict = verify(store)
        if cut in (0, len(full)):
            assert verdict.ok
        else:
            assert verdict.codes == ["TRUNCATED_TAIL"] and verdict.count == 0
            assert repair_truncate_partial_tail(store) == cut
            assert store.ledger_path.read_bytes() == b""
            assert verify(store).ok and verify(store).count == 0
    store.ledger_path.write_bytes(b"")
    freeze(store, protocol(), clock=clock_at(1))  # an emptied ledger starts again at seq 0
    assert entries(store)[0]["seq"] == 0


def test_garbage_appended_after_a_valid_ledger(tmp_path: Path) -> None:
    store, base = make_base(tmp_path / "s")
    for tail in (b"\x00" * 100, b"\xff\xfe", b'{"body"', b"\r", b" "):
        store.ledger_path.write_bytes(base + tail)
        assert verify(store).codes == ["TRUNCATED_TAIL"]
        assert repair_truncate_partial_tail(store) == len(tail)
        assert store.ledger_path.read_bytes() == base


def test_terminated_garbage_is_reported_but_not_repaired(tmp_path: Path) -> None:
    store, base = make_base(tmp_path / "s")
    store.ledger_path.write_bytes(base + b"junk\n")
    assert verify(store).codes == ["TRUNCATED_TAIL"]
    with pytest.raises(InputError) as info:
        repair_truncate_partial_tail(store)
    assert info.value.code == "NO_PARTIAL_TAIL"  # only an unterminated tail may be removed automatically
    assert store.ledger_path.read_bytes() == base + b"junk\n"


def test_repair_refuses_when_the_rest_is_corrupt(tmp_path: Path) -> None:
    store, base = make_base(tmp_path / "s")
    corrupt = base.replace(b'"seq":1', b'"seq":7', 1)
    assert corrupt != base
    store.ledger_path.write_bytes(corrupt + b'{"body":')
    with pytest.raises(VerificationFailed):
        repair_truncate_partial_tail(store)
    assert store.ledger_path.read_bytes() == corrupt + b'{"body":'


def test_repair_without_ledger(tmp_path: Path) -> None:
    with pytest.raises(EnvError) as info:
        repair_truncate_partial_tail(Store(tmp_path / "none"))
    assert info.value.code == "NO_LEDGER"


def test_scan_of_every_prefix_never_raises(tmp_path: Path) -> None:
    _, base = make_base(tmp_path / "s")
    for cut in range(len(base) + 1):
        verdict, _ = scan(base[:cut], card_hash)
        assert verdict.ok == (cut == 0 or base[cut - 1 : cut] == b"\n")
