# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from core_support import NOW, PROTOCOL_SHA, protocol, record_body

from protocolith.cli import main
from protocolith.core import ProtocolithError
from protocolith.core.errors import hint_for


@pytest.fixture(autouse=True)
def _clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROTOCOLITH_NOW", NOW)


def write(path: Path, value: Any) -> str:
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def files(tmp_path: Path) -> dict[str, str]:
    return {
        "protocol": write(tmp_path / "p.json", protocol()),
        "record": write(tmp_path / "r.json", record_body()),
        "deviation": write(
            tmp_path / "d.json", {"protocol_sha256": PROTOCOL_SHA, "kind": "source_change", "description": "moved"}
        ),
    }


def test_full_flow_human_output(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "st")]
    code, out, _ = run(capsys, "freeze", files["protocol"], *s)
    assert code == 0 and out.startswith("frozen DEMO_D001 1 seq=0 hash=")
    assert run(capsys, "deviation", files["deviation"], *s)[1].startswith("deviation source_change seq=1")
    assert run(capsys, "record", files["record"], *s)[1].startswith("recorded run-1 PASSED_UNDER_PROTOCOL seq=2")
    code, out, _ = run(capsys, "issue", "2", *s)
    lines = out.splitlines()
    assert code == 0 and lines[0].startswith("issued record seq=2 card_sha256=") and lines[1].endswith(".json")
    assert Path(lines[1]).is_file() and Path(lines[2]).is_file()
    code, out, _ = run(capsys, "verify-ledger", *s)
    assert code == 0 and out.startswith("OK entries=4 head seq=3 hash=")
    code, out, _ = run(capsys, "log", *s)
    assert [line.split()[1] for line in out.splitlines()] == ["freeze", "deviation", "record", "issue"]
    assert "record_seq=2" in out
    code, out, _ = run(capsys, "head", *s)
    assert code == 0 and out.startswith("seq=3 hash=")
    assert run(capsys, "validate-card", lines[1])[0] == 0  # existing commands keep working


def test_json_output_is_canonical(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "st"), "--json"]
    code, out, _ = run(capsys, "freeze", files["protocol"], *s)
    entry = json.loads(out)
    assert code == 0 and out == json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    out_dir = tmp_path / "cards"
    run(capsys, "record", files["record"], *s)
    code, out, _ = run(capsys, "issue", "1", "--out", str(out_dir), *s)
    assert code == 0 and (out_dir / "PLITH-DEMO_D001-2026-11-15-000001.svg").is_file()
    assert json.loads(out)["entry"]["body"]["record_seq"] == 1
    assert json.loads(run(capsys, "verify-ledger", *s)[1])["ok"] is True
    assert json.loads(run(capsys, "head", *s)[1])["seq"] == 2
    assert len(json.loads(run(capsys, "log", *s)[1])) == 3


def test_verification_failure_exit_1(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "st")]
    run(capsys, "freeze", files["protocol"], *s)
    ledger = tmp_path / "st" / "ledger.jsonl"
    ledger.write_bytes(ledger.read_bytes().replace(b"pass rate", b"pass RATE"))
    code, out, err = run(capsys, "verify-ledger", *s)
    assert code == 1 and out.startswith("FAILED: BAD_HASH") and "BAD_HASH line 0" in err
    code, out, err = run(capsys, "verify-ledger", "--json", *s)
    assert code == 1 and json.loads(out)["codes"] == ["BAD_HASH"]
    code, out, err = run(capsys, "log", "--json", *s)
    assert code == 1 and json.loads(out)["codes"] == ["BAD_HASH"] and "VERIFICATION_FAILED" in err


def test_input_errors_exit_2(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "st")]
    dup = tmp_path / "dup.json"
    dup.write_text('{"protocol_id":"X","protocol_id":"Y"}')
    code, out, err = run(capsys, "freeze", str(dup), *s, "--json")
    assert code == 2 and "DUPLICATE_KEY" in err and json.loads(out)["error"]["code"] == "DUPLICATE_KEY"
    floaty = tmp_path / "f.json"
    floaty.write_text('{"protocol_id":"X","version":"1","t":0.5}')
    assert run(capsys, "freeze", str(floaty), *s)[0] == 2
    assert run(capsys, "freeze", files["protocol"], *s)[0] == 0
    code, _, err = run(capsys, "freeze", files["protocol"], *s)
    assert code == 2 and "DUPLICATE_FREEZE" in err
    code, _, err = run(capsys, "issue", "0", *s)
    assert code == 2 and "DANGLING_REF" in err
    with pytest.raises(SystemExit) as info:
        main(["issue", "notanumber"])
    assert info.value.code == 2
    with pytest.raises(SystemExit) as info:
        main(["repair"])
    assert info.value.code == 2


def test_environment_errors_exit_3(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "none")]
    for command in ("verify-ledger", "log", "head"):
        code, _, err = run(capsys, command, *s)
        assert code == 3 and "NO_LEDGER" in err
    code, _, err = run(capsys, "freeze", str(tmp_path / "missing.json"), *s)
    assert code == 3 and "IO_ERROR" in err


def test_store_from_environment_and_default(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert run(capsys, "freeze", files["protocol"])[0] == 0
    assert (tmp_path / ".protocolith" / "ledger.jsonl").is_file()
    monkeypatch.setenv("PROTOCOLITH_STORE", str(tmp_path / "other"))
    assert run(capsys, "freeze", files["protocol"])[0] == 0
    assert (tmp_path / "other" / "ledger.jsonl").is_file()


def test_empty_head_and_verify_text(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    store = tmp_path / "e"
    store.mkdir()
    (store / "ledger.jsonl").write_bytes(b"")
    assert run(capsys, "head", "--store", str(store))[1] == "empty\n"
    assert run(capsys, "verify-ledger", "--store", str(store))[1] == "OK entries=0 empty\n"


def test_repair(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "st")]
    run(capsys, "freeze", files["protocol"], *s)
    ledger = tmp_path / "st" / "ledger.jsonl"
    good = ledger.read_bytes()
    ledger.write_bytes(good + b'{"bo')
    assert run(capsys, "verify-ledger", *s)[0] == 1
    code, out, _ = run(capsys, "repair", "--truncate-partial-tail", *s)
    assert code == 0 and out == "removed 4 bytes of partial tail\n" and ledger.read_bytes() == good
    code, _, err = run(capsys, "repair", "--truncate-partial-tail", *s)
    assert code == 2 and "NO_PARTIAL_TAIL" in err
    assert (
        json.loads(run(capsys, "repair", "--truncate-partial-tail", "--json", *s)[1])["error"]["code"]
        == "NO_PARTIAL_TAIL"
    )


def test_mcp_command_in_process(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Stream:
        def __init__(self, buffer: io.BytesIO) -> None:
            self.buffer = buffer

    out = io.BytesIO()
    monkeypatch.setattr(sys, "stdin", Stream(io.BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n')))
    monkeypatch.setattr(sys, "stdout", Stream(out))
    assert main(["mcp", "--store", str(tmp_path / "m")]) == 0
    assert json.loads(out.getvalue())["result"] == {}
    assert not (tmp_path / "m").exists()


def cli(tmp_path: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "protocolith.cli", *argv],
        capture_output=True, text=True, timeout=120, cwd=tmp_path, env={**os.environ, "PROTOCOLITH_NOW": NOW},
    )  # fmt: skip


def test_subprocess_exit_codes_and_flow(tmp_path: Path, files: dict[str, str]) -> None:
    s = ("--store", str(tmp_path / "st"))
    assert cli(tmp_path, "freeze", files["protocol"], *s).returncode == 0
    assert cli(tmp_path, "record", files["record"], *s).returncode == 0
    issued = cli(tmp_path, "issue", "1", *s)
    assert issued.returncode == 0 and issued.stderr == ""
    done = cli(tmp_path, "verify-ledger", *s, "--json")
    assert done.returncode == 0 and json.loads(done.stdout)["count"] == 3
    (tmp_path / "st" / "ledger.jsonl").write_bytes(b"{")
    assert cli(tmp_path, "verify-ledger", *s).returncode == 1
    assert cli(tmp_path, "freeze", "nofile.json", *s).returncode == 3
    assert cli(tmp_path, "issue", "x").returncode == 2


@pytest.fixture
def filled(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> list[str]:
    s = ["--store", str(tmp_path / "st")]
    run(capsys, "freeze", files["protocol"], *s)
    run(capsys, "deviation", files["deviation"], *s)
    run(capsys, "record", files["record"], *s)
    run(capsys, "issue", "2", *s)
    return s


def test_summary_text_and_json(capsys: pytest.CaptureFixture[str], filled: list[str]) -> None:
    code, out, _ = run(capsys, "summary", *filled)
    lines = out.splitlines()
    assert code == 0 and lines[0].startswith("ledger OK  entries=4  head seq=3 hash=")
    assert lines[1] == "entries: freeze 1, record 1, deviation 1, issue 1"
    assert lines[2] == "results: PASSED_UNDER_PROTOCOL 1"
    assert lines[3].split() == ["PROTOCOL", "VERSIONS", "LATEST", "RECORDS", "LATEST_STATUS", "DEVIATIONS", "CARDS"]
    assert lines[4].split() == ["DEMO_D001", "1", "1", "1", "PASSED_UNDER_PROTOCOL", "1", "1"]
    assert lines[3].index("VERSIONS") == lines[4].index("1", 10) and lines[-1] == "problems: none"
    code, out, _ = run(capsys, "summary", "--protocol", "DEMO_D001", "--json", *filled)
    assert code == 0 and json.loads(out)["protocols"][0]["records"] == 1
    assert run(capsys, "summary", "--protocol", "NOPE", *filled)[0] == 2


def test_summary_of_empty_and_damaged_ledgers(capsys: pytest.CaptureFixture[str], tmp_path: Path, filled: list[str]) -> None:
    empty = ["--store", str(tmp_path / "e")]
    assert run(capsys, "init", *empty)[0] == 0
    code, out, _ = run(capsys, "summary", *empty)
    assert code == 0 and out.splitlines()[0] == "ledger OK  entries=0  empty" and "results: none" in out
    ledger = tmp_path / "st" / "ledger.jsonl"
    ledger.write_bytes(ledger.read_bytes().replace(b"pass rate", b"pass RATE"))
    code, out, _ = run(capsys, "summary", *filled)
    assert code == 1 and out.startswith("ledger FAILED") and "problems: none" not in out and "BAD_HASH line 0" in out


def test_log_filters_and_show(capsys: pytest.CaptureFixture[str], filled: list[str]) -> None:
    out = run(capsys, "log", "--type", "record", *filled)[1]
    assert [line.split()[:2] for line in out.splitlines()] == [["2", "record"]]
    assert len(run(capsys, "log", "--protocol", "DEMO_D001", "--tail", "2", *filled)[1].splitlines()) == 2
    assert run(capsys, "log", "--status", "PASSED_UNDER_PROTOCOL", *filled)[1].startswith("2 record")
    assert json.loads(run(capsys, "log", "--tail", "1", "--json", *filled)[1])[0]["seq"] == 3
    assert run(capsys, "log", "--tail", "0", *filled)[0] == 2
    with pytest.raises(SystemExit):
        main(["log", "--type", "nope"])
    code, out, _ = run(capsys, "show", "2", *filled)
    assert code == 0 and "protocol DEMO_D001 1 (frozen at seq 0)" in out
    assert "points at: 1" not in out and "pointed at by: 3" in out and out.splitlines()[-1].startswith("body: {")
    assert "points at: -" in run(capsys, "show", "0", *filled)[1]
    shown = json.loads(run(capsys, "show", "3", "--json", *filled)[1])
    assert shown["points_at"] == [2] and shown["protocol"]["protocol_id"] == "DEMO_D001"
    assert run(capsys, "show", "9", *filled)[0] == 2


def test_init_is_idempotent(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    s = ["--store", str(tmp_path / "new")]
    code, out, _ = run(capsys, "init", *s)
    assert code == 0 and out == f"created {tmp_path / 'new'}\n"
    assert run(capsys, "init", *s)[1] == f"exists {tmp_path / 'new'}\n"
    assert json.loads(run(capsys, "init", "--json", *s)[1]) == {"created": False, "path": str(tmp_path / "new")}
    assert run(capsys, "head", *s)[1] == "empty\n" and run(capsys, "freeze", files["protocol"], *s)[0] == 0


def test_capture_and_schema_commands(capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "data.csv").write_text("a,b\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    code, out, _ = run(capsys, "capture", "--file", "data.csv")
    found = json.loads(out)
    assert code == 0 and found["inputs"][0]["path"] == "data.csv" and "environment" not in found
    assert set(json.loads(run(capsys, "capture", "--env")[1])) == {"environment", "inputs"}
    code, out, err = run(capsys, "capture", "--file", "../x")
    assert code == 2 and "BAD_PATH" in err and "hint (BAD_PATH)" in err
    assert json.loads(run(capsys, "capture", "--file", "nope", "--json")[1])["error"]["code"] == "BAD_PATH"
    assert json.loads(run(capsys, "schema", "record")[1])["title"] == "protocolith record"
    assert set(json.loads(run(capsys, "schema")[1])) == {"freeze", "record", "deviation", "issue", "entry"}
    with pytest.raises(SystemExit):
        main(["schema", "nope"])


def test_errors_carry_a_hint(capsys: pytest.CaptureFixture[str], tmp_path: Path, files: dict[str, str]) -> None:
    code, _, err = run(capsys, "head", "--store", str(tmp_path / "none"))
    assert code == 3 and "hint (NO_LEDGER): run `protocolith freeze FILE`" in err
    s = ["--store", str(tmp_path / "st")]
    run(capsys, "freeze", files["protocol"], *s)
    code, out, err = run(capsys, "verify-ledger", "--expect-head", "0:" + "e" * 64, *s)
    assert code == 1 and "hint (HEAD_MISMATCH)" in err
    code, out, _ = run(capsys, "freeze", files["protocol"], "--json", *s)
    assert json.loads(out)["error"] == {
        "code": "DUPLICATE_FREEZE",
        "hint": hint_for("DUPLICATE_FREEZE"),
        "message": "DEMO_D001 version 1 is already frozen",
    }
    assert "hint" not in ProtocolithError("NO_SUCH_CODE", "x").to_dict()["error"]
    ledger = tmp_path / "st" / "ledger.jsonl"
    ledger.write_bytes(ledger.read_bytes() + b'{"bo')
    assert "hint (TRUNCATED_TAIL): a write was interrupted" in run(capsys, "verify-ledger", *s)[2]
