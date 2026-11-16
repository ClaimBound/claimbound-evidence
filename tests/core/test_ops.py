# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from core_support import CARD, HASH_A, NOW, PROTOCOL_SHA, clock, deviation_body, protocol, record_body

from protocolith.core import (
    EnvError,
    ProtocolithError,
    Store,
    VerificationFailed,
    deviation,
    entries,
    freeze,
    head,
    issue,
    now_utc,
    record,
    repair_truncate_partial_tail,
    resolve_store,
    verify,
)
from protocolith.core.ledger import MAX_ENTRY_BYTES


def raises(code: str, call: Any, *args: Any, **kwargs: Any) -> ProtocolithError:
    with pytest.raises(ProtocolithError) as info:
        call(*args, **kwargs)
    assert info.value.code == code
    return info.value


def ledger_bytes(store: Store) -> bytes:
    return store.ledger_path.read_bytes()


def test_full_flow_through_the_python_api(store: Store, tmp_path: Path) -> None:
    first = freeze(store, protocol(), clock=clock(NOW))
    assert first["seq"] == 0 and first["body"]["protocol_sha256"] == PROTOCOL_SHA
    dev = deviation(store, deviation_body(), clock=clock(NOW))
    rec = record(store, record_body(deviations=[1]), clock=clock("2026-11-15T10:00:01Z"))
    assert (dev["seq"], rec["seq"]) == (1, 2)
    result = issue(store, 2, clock=clock("2026-11-15T10:00:02Z"))
    assert result["card"]["evidence_id"] == "PLITH-DEMO_D001-2026-11-15-000002"
    assert Path(result["json_path"]).parent == store.cards_dir
    assert Path(result["svg_path"]).read_text(encoding="utf-8").startswith("<?xml")
    verdict = verify(store)
    assert verdict.ok and verdict.count == 4
    assert [e["type"] for e in entries(store)] == ["freeze", "deviation", "record", "issue"]
    assert head(store) == {"count": 4, "hash": verdict.head_hash, "seq": 3}


def test_card_file_hash_matches_the_issue_entry(recorded: Store) -> None:
    import hashlib

    result = issue(recorded, 1, clock=clock(NOW))
    data = Path(result["json_path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == result["entry"]["body"]["card_sha256"]


def test_issue_to_custom_out_dir_and_reissue(recorded: Store, tmp_path: Path) -> None:
    out = tmp_path / "elsewhere"
    first = issue(recorded, 1, out=out, clock=clock(NOW))
    again = issue(recorded, 1, out=out, clock=clock(NOW))
    assert Path(first["json_path"]).parent == out
    assert again["entry"]["seq"] == first["entry"]["seq"] + 1
    assert verify(recorded).ok


def test_card_exists_with_different_content(recorded: Store, tmp_path: Path) -> None:
    out = tmp_path / "cards"
    out.mkdir()
    (out / "PLITH-DEMO_D001-2026-11-15-000001.json").write_bytes(b"{}")
    raises("CARD_EXISTS", issue, recorded, 1, out=out, clock=clock(NOW))
    assert verify(recorded).count == 2


def test_issue_argument_errors(recorded: Store) -> None:
    raises("BAD_ENTRY", issue, recorded, "1")
    raises("BAD_ENTRY", issue, recorded, True)
    raises("DANGLING_REF", issue, recorded, 0)
    raises("DANGLING_REF", issue, recorded, 99)


def test_issue_names_missing_card_fields(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    card = dict(CARD)
    del card["operator"]
    del card["baseline_control_summary"]
    del card["public_claim_text"]
    record(store, record_body(card=card), clock=clock(NOW))
    err = raises("MISSING_FIELD", issue, store, 1, clock=clock(NOW))
    for name in ("operator", "baseline_control_summary", "public_claim_text"):
        assert name in err.message
    assert verify(store).count == 2


def test_issue_without_card_metadata(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(card=None), clock=clock(NOW))
    err = raises("MISSING_FIELD", issue, store, 1, clock=clock(NOW))
    assert "operator" in err.message


def test_issue_invalid_card_value(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(card={**CARD, "execution_mode": "MAGIC"}), clock=clock(NOW))
    raises("CARD_INVALID", issue, store, 1, clock=clock(NOW))


def test_card_cannot_contradict_the_record(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(card={**CARD, "result_status": "BLOCKED_SOURCE"}), clock=clock(NOW))
    err = raises("CARD_CONFLICT", issue, store, 1, clock=clock(NOW))
    assert "result_status" in err.message


def test_card_extra_matching_the_record_is_accepted(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(card={**CARD, "result_status": "PASSED_UNDER_PROTOCOL"}), clock=clock(NOW))
    assert issue(store, 1, clock=clock(NOW))["card"]["result_status"] == "PASSED_UNDER_PROTOCOL"


def test_freeze_rejections_leave_the_ledger_untouched(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    before = ledger_bytes(store)
    err = raises("DUPLICATE_FREEZE", freeze, store, protocol(), clock=clock(NOW))
    assert err.violations and err.exit_code == 2
    raises("DUPLICATE_FREEZE", freeze, store, {**protocol(), "gate": "changed"}, clock=clock(NOW))
    raises("MISSING_FIELD", freeze, store, {"version": "2"}, clock=clock(NOW))
    raises("BAD_ENTRY", freeze, store, ["not", "an", "object"])
    raises("FLOAT_NOT_ALLOWED", freeze, store, {**protocol(), "version": "3", "x": 0.5})
    raises("UNKNOWN_PROTOCOL", freeze, store, {**protocol(), "version": "3"}, supersedes=HASH_A, clock=clock(NOW))
    assert ledger_bytes(store) == before


def test_new_version_supersedes_and_old_record_stays_valid(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    new = freeze(store, {**protocol(), "version": "2"}, supersedes=PROTOCOL_SHA, clock=clock(NOW))
    assert new["body"]["supersedes"] == PROTOCOL_SHA
    record(store, record_body(), clock=clock(NOW))
    assert verify(store).ok


def test_record_rejections(store: Store) -> None:
    raises("UNKNOWN_PROTOCOL", record, store, record_body(), clock=clock(NOW))
    freeze(store, protocol(), clock=clock(NOW))
    raises("BAD_ENTRY", record, store, "x")
    raises("BAD_ENTRY", deviation, store, 5)
    raises("BAD_STATUS", record, store, record_body(status="BEST_MODEL"), clock=clock(NOW))
    raises("MISSING_FIELD", record, store, record_body(status="BLOCKED_SOURCE"), clock=clock(NOW))
    raises("DANGLING_REF", record, store, record_body(deviations=[0]), clock=clock(NOW))
    raises("FLOAT_NOT_ALLOWED", record, store, record_body(outcome={"x": 0.5}))
    assert verify(store).count == 1


def test_limits(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    raises("ENTRY_TOO_LARGE", record, store, record_body(outcome={"note": "x" * MAX_ENTRY_BYTES}), clock=clock(NOW))
    deep: Any = []
    for _ in range(70):
        deep = [deep]
    raises("TOO_DEEP", record, store, record_body(outcome={"d": deep}), clock=clock(NOW))
    assert verify(store).count == 1


def test_clock_injection_and_environment(store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    assert now_utc(clock("2026-01-02T03:04:05Z")) == "2026-01-02T03:04:05Z"
    monkeypatch.setenv("PROTOCOLITH_NOW", "2026-02-03T04:05:06Z")
    assert now_utc() == "2026-02-03T04:05:06Z"
    assert now_utc(clock(NOW)) == NOW
    assert freeze(store, protocol())["ts"] == "2026-02-03T04:05:06Z"
    monkeypatch.setenv("PROTOCOLITH_NOW", "yesterday")
    raises("BAD_CLOCK", now_utc)
    raises("BAD_CLOCK", now_utc, clock("2026-13-45T00:00:00Z"))
    monkeypatch.delenv("PROTOCOLITH_NOW")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", now_utc())


def test_time_going_backwards_is_rejected(recorded: Store) -> None:
    before = ledger_bytes(recorded)
    raises("TS_REGRESSION", deviation, recorded, deviation_body(), clock=clock("2026-11-15T09:59:59Z"))
    assert ledger_bytes(recorded) == before


def test_reads_on_a_missing_ledger(store: Store) -> None:
    for call in (verify, entries, head):
        assert raises("NO_LEDGER", call, store).exit_code == 3
    raises("NO_LEDGER", repair_truncate_partial_tail, store)


def test_head_and_entries_of_an_empty_ledger(store: Store) -> None:
    store.path.mkdir()
    store.ledger_path.write_bytes(b"")
    assert head(store) == {"count": 0, "hash": None, "seq": None}
    assert entries(store) == []
    assert verify(store).ok


def test_string_paths_are_accepted(tmp_path: Path) -> None:
    freeze(str(tmp_path / "s"), protocol(), clock=clock(NOW))
    assert verify(tmp_path / "s").ok  # type: ignore[arg-type]


def test_resolve_store_order(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert resolve_store("a").path == Path("a")
    assert resolve_store(None).path == Path(".protocolith")
    monkeypatch.setenv("PROTOCOLITH_STORE", str(tmp_path / "env"))
    assert resolve_store(None).path == tmp_path / "env"
    assert resolve_store("explicit").path == Path("explicit")


def test_tamper_is_detected_and_blocks_appends(recorded: Store) -> None:
    data = ledger_bytes(recorded).replace(b"run-1", b"run-2")
    recorded.ledger_path.write_bytes(data)
    verdict = verify(recorded)
    assert verdict.codes == ["BAD_HASH"]
    err = raises("VERIFICATION_FAILED", record, recorded, record_body(), clock=clock(NOW))
    assert isinstance(err, VerificationFailed) and err.exit_code == 1 and err.codes() == ["BAD_HASH"]
    raises("VERIFICATION_FAILED", entries, recorded)
    raises("VERIFICATION_FAILED", issue, recorded, 1)


def test_removed_head_changes_head_record(recorded: Store) -> None:
    before = head(recorded)
    lines = ledger_bytes(recorded).splitlines(keepends=True)
    recorded.ledger_path.write_bytes(lines[0])
    assert head(recorded) != before and verify(recorded).ok


def test_crash_simulation_partial_tail_and_repair(recorded: Store) -> None:
    good = ledger_bytes(recorded)
    recorded.ledger_path.write_bytes(good + b'{"body":{"kind":"sour')
    verdict = verify(recorded)
    assert verdict.codes == ["TRUNCATED_TAIL"] and verdict.count == 2
    raises("VERIFICATION_FAILED", deviation, recorded, deviation_body(), clock=clock(NOW))
    assert repair_truncate_partial_tail(recorded) == len(b'{"body":{"kind":"sour')
    assert ledger_bytes(recorded) == good
    deviation(recorded, deviation_body(), clock=clock(NOW))
    assert verify(recorded).ok


def test_repair_refuses_when_nothing_to_repair_or_rest_is_damaged(recorded: Store) -> None:
    raises("NO_PARTIAL_TAIL", repair_truncate_partial_tail, recorded)
    damaged = ledger_bytes(recorded).replace(b"run-1", b"run-2") + b"{"
    recorded.ledger_path.write_bytes(damaged)
    raises("VERIFICATION_FAILED", repair_truncate_partial_tail, recorded)
    assert ledger_bytes(recorded) == damaged


def test_repair_of_a_file_holding_only_a_partial_line(store: Store) -> None:
    store.path.mkdir()
    store.ledger_path.write_bytes(b'{"bo')
    assert repair_truncate_partial_tail(store) == 4
    assert store.ledger_path.read_bytes() == b""


def test_io_errors_become_env_errors(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x")
    err = raises("IO_ERROR", freeze, Store(blocker / "sub"), protocol(), clock=clock(NOW))
    assert err.exit_code == 3
    adir = Store(tmp_path / "d")
    adir.path.mkdir()
    adir.ledger_path.mkdir()
    raises("IO_ERROR", verify, adir)
    ldir = Store(tmp_path / "l")
    ldir.path.mkdir()
    ldir.lock_path.mkdir()
    raises("IO_ERROR", freeze, ldir, protocol(), clock=clock(NOW))


def test_reader_without_a_lock_file_still_reads(recorded: Store) -> None:
    recorded.lock_path.unlink()
    assert verify(recorded).ok
    assert not recorded.lock_path.exists()


def test_lock_timeout_and_release(recorded: Store) -> None:
    quick = Store(recorded.path, lock_timeout=0.05)
    with recorded.locked(write=True):
        err = raises("LOCK_TIMEOUT", verify, quick)
        assert isinstance(err, EnvError)
    assert verify(quick).ok


def test_two_processes_append_concurrently(store: Store, tmp_path: Path) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    script = tmp_path / "worker.py"
    script.write_text(
        textwrap.dedent(
            """
            import sys
            from protocolith.core import record
            sys.path.insert(0, sys.argv[2])
            from core_support import record_body
            for number in range(15):
                record(sys.argv[1], record_body(run_id=f"{sys.argv[3]}-{number}"))
            """
        )
    )
    env = {**os.environ, "PROTOCOLITH_NOW": NOW}
    here = str(Path(__file__).parent)
    procs = [
        subprocess.Popen([sys.executable, "-I", str(script), str(store.path), here, name], env=env)
        for name in ("a", "b")
    ]
    assert [p.wait(timeout=120) for p in procs] == [0, 0]
    verdict = verify(store)
    assert verdict.ok and verdict.count == 31
    runs = sorted(e["body"]["run_id"] for e in entries(store)[1:])
    assert runs == sorted(f"{n}-{i}" for n in "ab" for i in range(15))


def test_blocked_record_card_carries_the_reason(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    card = {k: v for k, v in CARD.items() if k != "baseline_control_summary"}
    body = record_body(status="BLOCKED_SOURCE", block_reason="The source returned HTTP 403.", sources=[], card=card)
    record(store, body, clock=clock(NOW))
    result = issue(store, 1, clock=clock(NOW))
    assert result["card"]["block_reason"] == "The source returned HTTP 403."
    assert result["card"]["result_status"] == "BLOCKED_SOURCE"


def test_build_card_for_an_unfrozen_protocol() -> None:
    from protocolith.core import scan
    from protocolith.core.issue import build_card
    from protocolith.core.ledger import ZERO_HASH, make_entry, serialize

    entry = make_entry(seq=0, prev=ZERO_HASH, ts=NOW, type="record", body=record_body())
    verifier = scan(serialize(entry))[1]
    raises("UNKNOWN_PROTOCOL", build_card, verifier, 0)


def test_two_records_of_one_protocol_on_one_day_both_issue(recorded: Store) -> None:
    record(recorded, record_body(run_id="run-2"), clock=clock(NOW))
    first = issue(recorded, 1, clock=clock(NOW))
    second = issue(recorded, 2, clock=clock(NOW))
    assert first["card"]["evidence_id"] == "PLITH-DEMO_D001-2026-11-15-000001"
    assert second["card"]["evidence_id"] == "PLITH-DEMO_D001-2026-11-15-000002"
    assert verify(recorded).ok
