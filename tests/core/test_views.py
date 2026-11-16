# SPDX-License-Identifier: Apache-2.0
"""summary, filtered log, show and init (Python API), plus capture."""

from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest
from core_support import NOW, PROTOCOL_SHA, clock, deviation_body, protocol, record_body

from protocolith.core import (
    InputError, ProtocolithError, Store, capture, deviation, freeze, head, init, issue, log, record, show, summary, verify,
)  # fmt: skip
from protocolith.core.ledger import CARD_FORMAT, make_entry, serialize
from protocolith.core.rules import scan
from protocolith.core.views import show as view_show
from protocolith.core.capture import describe_file, environment

capture_module = importlib.import_module("protocolith.core.capture")
PROTOCOL_V2 = {**protocol(), "version": "2"}


def raises(code: str, call: Any, *args: Any, **kwargs: Any) -> None:
    with pytest.raises(ProtocolithError) as info:
        call(*args, **kwargs)
    assert info.value.code == code


@pytest.fixture
def busy(store: Store) -> Store:
    """freeze v1, deviation, blocked record, passed record, issue of it, freeze v2 and another protocol."""
    c = clock(NOW)
    freeze(store, protocol(), clock=c)  # 0
    deviation(store, deviation_body(), clock=c)  # 1
    record(store, record_body(status="BLOCKED_SOURCE", block_reason="robots", sources=[], deviations=[1]), clock=c)  # 2
    record(store, record_body(run_id="run-2"), clock=c)  # 3
    issue(store, 3, clock=c)  # 4
    freeze(store, PROTOCOL_V2, supersedes=PROTOCOL_SHA, clock=c)  # 5
    freeze(store, {"protocol_id": "OTHER_D001", "version": "1"}, clock=c)  # 6
    return store


def test_summary_of_a_busy_ledger(busy: Store) -> None:
    found = summary(busy)
    assert found["ok"] is True and found["problems"] == []
    assert found["head"] == {"count": 7, "hash": head(busy)["hash"], "seq": 6}
    assert found["entries_by_type"] == {"freeze": 3, "record": 2, "deviation": 1, "issue": 1}
    assert found["records_by_status"] == {"BLOCKED_SOURCE": 1, "PASSED_UNDER_PROTOCOL": 1}
    demo, other = found["protocols"]
    assert demo == {
        "cards": 1, "deviations": 1, "latest_status": "PASSED_UNDER_PROTOCOL", "latest_version": "2",
        "protocol_id": "DEMO_D001", "records": 2, "versions": ["1", "2"],
    }  # fmt: skip
    assert other["protocol_id"] == "OTHER_D001" and other["latest_status"] is None and other["records"] == 0


def test_summary_can_be_limited_to_one_protocol(busy: Store) -> None:
    found = summary(busy, "OTHER_D001")
    assert [row["protocol_id"] for row in found["protocols"]] == ["OTHER_D001"]
    assert found["entries_by_type"] == {"freeze": 1, "record": 0, "deviation": 0, "issue": 0}
    assert found["records_by_status"] == {}
    raises("UNKNOWN_PROTOCOL", summary, busy, "NOPE")


def test_summary_of_an_empty_and_a_missing_ledger(store: Store) -> None:
    raises("NO_LEDGER", summary, store)
    init(store)
    found = summary(store)
    assert found["ok"] and found["head"] == {"count": 0, "hash": None, "seq": None} and found["protocols"] == []


def test_summary_reports_problems_instead_of_raising(busy: Store) -> None:
    data = busy.ledger_path.read_bytes()
    busy.ledger_path.write_bytes(data.replace(b'"run_id":"run-2"', b'"run_id":"run-9"'))
    assert not verify(busy).ok
    found = summary(busy)
    assert found["ok"] is False and found["problems"][0]["code"] == "BAD_HASH"


def damaged(store: Store) -> Store:
    """A ledger with a record of an unfrozen protocol and an issue of a record that does not exist."""
    freeze(store, protocol(), clock=clock(NOW))
    tip = head(store)["hash"]
    stray = make_entry(seq=1, prev=tip, ts=NOW, type="record", body=record_body(protocol_sha256="c" * 64))
    ghost = make_entry(
        seq=2, prev=stray["hash"], ts=NOW, type="issue", body={"card_sha256": "d" * 64, "format": CARD_FORMAT, "record_seq": 7}
    )
    store.append_line(serialize(stray) + serialize(ghost))
    return store


def test_entries_of_unknown_protocols_are_reported_but_not_tabulated(store: Store) -> None:
    found = summary(damaged(store))
    assert found["ok"] is False and {p["code"] for p in found["problems"]} == {"UNKNOWN_PROTOCOL", "DANGLING_REF"}
    assert [row["protocol_id"] for row in found["protocols"]] == ["DEMO_D001"]
    assert found["entries_by_type"] == {"freeze": 1, "record": 0, "deviation": 0, "issue": 0}
    assert show_unverified(store, 1)["protocol"] is None and show_unverified(store, 2)["points_at"] == [7]


def show_unverified(store: Store, seq: int) -> dict[str, Any]:
    return view_show(scan(store.read(missing_ok=False))[1], seq)


def test_log_filters(busy: Store) -> None:
    assert [e["seq"] for e in log(busy)] == list(range(7))
    assert [e["seq"] for e in log(busy, type="record")] == [2, 3]
    assert [e["seq"] for e in log(busy, status="BLOCKED_SOURCE")] == [2]
    assert [e["seq"] for e in log(busy, protocol="DEMO_D001")] == [0, 1, 2, 3, 4, 5]
    assert [e["seq"] for e in log(busy, protocol="DEMO_D001", type="issue")] == [4]
    assert [e["seq"] for e in log(busy, tail=2)] == [5, 6]
    assert [e["seq"] for e in log(busy, protocol="DEMO_D001", type="record", tail=1)] == [3]
    assert log(busy, type="issue", status="BLOCKED_SOURCE") == []
    raises("BAD_ENTRY", log, busy, type="nope")
    raises("BAD_STATUS", log, busy, status="nope")
    raises("BAD_ENTRY", log, busy, tail=0)
    raises("BAD_ENTRY", log, busy, tail=True)
    raises("UNKNOWN_PROTOCOL", log, busy, protocol="NOPE")


def test_show_gives_context_and_references(busy: Store) -> None:
    blocked = show(busy, 2)
    assert blocked["entry"]["seq"] == 2 and blocked["points_at"] == [1] and blocked["pointed_by"] == []
    assert blocked["protocol"] == {"freeze_seq": 0, "protocol_id": "DEMO_D001", "protocol_sha256": PROTOCOL_SHA, "version": "1"}
    assert show(busy, 1)["pointed_by"] == [2]
    assert show(busy, 3)["pointed_by"] == [4] and show(busy, 4)["points_at"] == [3]
    assert show(busy, 4)["protocol"]["protocol_id"] == "DEMO_D001"
    assert show(busy, 0)["protocol"]["freeze_seq"] == 0 and show(busy, 0)["points_at"] == []
    raises("DANGLING_REF", show, busy, 99)
    raises("DANGLING_REF", show, busy, "1")
    raises("DANGLING_REF", show, busy, True)


def test_init_creates_an_empty_ledger_and_is_idempotent(tmp_path: Path) -> None:
    store = Store(tmp_path / "new" / "st")
    first = init(store)
    assert first == {"created": True, "path": str(store.path)} and store.ledger_path.read_bytes() == b""
    assert init(store)["created"] is False
    assert verify(store).ok and head(store)["count"] == 0 and log(store) == []
    freeze(store, protocol(), clock=clock(NOW))
    assert init(store)["created"] is False and verify(store).count == 1


def test_capture_describes_files_and_environment(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.bin").write_bytes(b"x" * 3_000_000)
    (tmp_path / "b.txt").write_text("hello", encoding="utf-8")
    found = capture(["sub/a.bin", "b.txt"], base=tmp_path)
    assert found == {
        "inputs": [
            {"path": "sub/a.bin", "sha256": hashlib.sha256(b"x" * 3_000_000).hexdigest(), "size": 3_000_000},
            {"path": "b.txt", "sha256": hashlib.sha256(b"hello").hexdigest(), "size": 5},
        ]
    }
    with_env = capture(["b.txt"], env=True, base=tmp_path)
    assert set(with_env["environment"]) == {"machine", "platform", "protocolith", "python"}
    assert with_env["environment"]["platform"] == sys.platform
    assert capture(base=tmp_path)["inputs"] == [] and "environment" in capture(base=tmp_path)
    assert str(tmp_path) not in str(found)


def test_capture_refuses_paths_outside_or_not_files(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    (work / "link").symlink_to(tmp_path / "outside.txt")
    for name in ("../outside.txt", str(tmp_path / "outside.txt"), "link", "missing.txt", "."):
        with pytest.raises(InputError) as info:
            describe_file(name, work)
        assert info.value.code == "BAD_PATH"
    raises("IO_ERROR", describe_file, "bad\0name", work)


def test_capture_without_an_installed_distribution(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> str:
        raise capture_module.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(capture_module.metadata, "version", missing)
    assert environment()["protocolith"] == "unknown"
