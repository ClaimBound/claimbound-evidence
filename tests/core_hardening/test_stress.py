# SPDX-License-Identifier: Apache-2.0
"""Heavier scenarios, run with ``-m slow``: concurrency, big ledgers, limits, odd paths, read-only stores."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from hardening_support import PROTOCOL_SHA, clock_at, deviation_body, fast_ledger, protocol, record_body, ts

from protocolith.cli import main
from protocolith.core import (
    EnvError,
    InputError,
    Store,
    VerificationFailed,
    decode,
    deviation,
    encode,
    entries,
    freeze,
    issue,
    record,
    scan,
    verify,
)
from protocolith.core.issue import card_hash
from protocolith.core.ledger import MAX_ENTRY_BYTES, make_entry, serialize

pytestmark = pytest.mark.slow

WORKER = textwrap.dedent(
    """
    import sys
    from protocolith.core import Store, deviation
    store = Store(sys.argv[1], lock_timeout=300.0)
    body = {"protocol_sha256": sys.argv[2], "kind": "k" + sys.argv[3], "description": "d"}
    for i in range(int(sys.argv[4])):
        deviation(store, {**body, "description": f"worker {sys.argv[3]} entry {i}"})
    """
)


def test_eight_processes_append_200_each(tmp_path: Path) -> None:
    store = Store(tmp_path / "s")
    freeze(store, protocol(), clock=clock_at(0))
    procs = [
        subprocess.Popen([sys.executable, "-c", WORKER, str(store.path), PROTOCOL_SHA, str(n), "200"], stderr=subprocess.PIPE)
        for n in range(8)
    ]
    errors = [p.communicate(timeout=1500)[1].decode() for p in procs]
    assert [p.returncode for p in procs] == [0] * 8, errors
    verdict = verify(store)
    assert verdict.ok, verdict.violations[:3]
    assert verdict.count == 1 + 8 * 200
    found = entries(store)
    assert [e["seq"] for e in found] == list(range(1601))
    per_worker: dict[str, list[str]] = {}
    for entry in found[1:]:
        _, worker, _, index = entry["body"]["description"].split()
        per_worker.setdefault(worker, []).append(index)
    assert all(order == [str(i) for i in range(200)] for order in per_worker.values())  # each worker's order kept


def test_a_20000_entry_ledger_verifies(tmp_path: Path) -> None:
    data = fast_ledger(20_000)
    verdict, verifier = scan(data, card_hash)
    assert verdict.ok and verdict.count == 20_000 and verdict.head_seq == 19_999
    store = Store(tmp_path / "s")
    store.path.mkdir()
    store.ledger_path.write_bytes(data)
    assert verify(store).count == 20_000
    deviation(store, deviation_body(), clock=clock_at(1))
    assert verify(store).count == 20_001
    assert verifier.index == 20_000


def entry_size(description_chars: int) -> int:
    entry = make_entry(seq=1, prev="0" * 64, ts=ts(0), type="deviation", body=deviation_body(description="x" * description_chars))
    return len(serialize(entry)) - 1


def test_entry_size_limit_exact_boundary(tmp_path: Path) -> None:
    base = entry_size(0)
    store = Store(tmp_path / "s")
    freeze(store, protocol(), clock=clock_at(0))
    assert base + (MAX_ENTRY_BYTES - base) == MAX_ENTRY_BYTES
    fits = MAX_ENTRY_BYTES - base
    assert entry_size(fits) == MAX_ENTRY_BYTES and entry_size(fits + 1) == MAX_ENTRY_BYTES + 1
    before = store.ledger_path.read_bytes()
    with pytest.raises(InputError) as info:
        deviation(store, deviation_body(description="x" * (fits + 1)), clock=clock_at(1))
    assert info.value.code == "ENTRY_TOO_LARGE" and store.ledger_path.read_bytes() == before
    entry = deviation(store, deviation_body(description="x" * fits), clock=clock_at(1))
    assert len(serialize(entry)) - 1 == MAX_ENTRY_BYTES
    assert verify(store).ok
    assert deviation(store, deviation_body(), clock=clock_at(2))["seq"] == 2  # the ledger stays usable
    # An oversized line written by hand is reported, once, as ENTRY_TOO_LARGE.
    big = make_entry(seq=3, prev=entries(store)[-1]["hash"], ts=ts(3), type="deviation", body=deviation_body(description="x" * (fits + 1)))
    store.ledger_path.write_bytes(store.ledger_path.read_bytes() + serialize(big))
    assert verify(store).codes == ["ENTRY_TOO_LARGE"]


def nested(depth: int) -> Any:
    value: Any = []
    for _ in range(depth - 1):
        value = [value]
    return value


@pytest.mark.parametrize("depth", [63, 64, 65])
def test_nesting_depth_at_the_limit(depth: int) -> None:
    text = "[" * depth + "]" * depth
    if depth <= 64:
        assert encode(decode(text)) == text.encode() and encode(nested(depth)) == text.encode()
    else:
        for call in (lambda: decode(text), lambda: encode(nested(depth))):
            with pytest.raises(InputError) as info:
                call()
            assert info.value.code == "TOO_DEEP"


@pytest.mark.parametrize("inner_depth", [60, 61, 62, 63, 64])
def test_nesting_inside_a_ledger_entry(tmp_path: Path, inner_depth: int) -> None:
    """The entry object and its body take two levels, so a protocol may nest 62 levels and no more."""
    store = Store(tmp_path / "s")
    proto = {"gate": nested(inner_depth - 1), "protocol_id": "DEEP", "version": "1"}  # protocol itself has depth inner_depth
    if inner_depth <= 62:
        entry = freeze(store, proto, clock=clock_at(0))
        assert verify(store).ok and entry["body"]["protocol"] == proto
    else:
        with pytest.raises(InputError) as info:
            freeze(store, proto, clock=clock_at(0))
        assert info.value.code == "TOO_DEEP"
        assert not store.ledger_path.exists()


def full_flow(store: Store, out: Path | None = None) -> None:
    freeze(store, protocol(), clock=clock_at(0))
    record(store, record_body(), clock=clock_at(1))
    issued = issue(store, 1, out=out, clock=clock_at(2))
    assert Path(issued["json_path"]).is_file() and Path(issued["svg_path"]).is_file()
    assert verify(store).count == 3


@pytest.mark.parametrize("name", ["with space", "ünïcödé 日本語", "emoji \U0001f600 dir", "dots.and-dashes_1", "a" * 100])
def test_unusual_store_and_output_paths(tmp_path: Path, name: str) -> None:
    full_flow(Store(tmp_path / name / "store dir"), tmp_path / name / "out cards ü")
    code = main(["verify-ledger", "--store", str(tmp_path / name / "store dir")])
    assert code == 0


def test_paths_through_environment_and_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    real = tmp_path / "real store ü"
    real.mkdir()  # a dangling symlink is refused by mkdir (IO_ERROR), so the target must exist
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    monkeypatch.setenv("PROTOCOLITH_STORE", str(link))
    full_flow(Store(link))
    assert main(["head"]) == 0 and "seq=2" in capsys.readouterr().out
    assert (real / "ledger.jsonl").is_file()


def test_crlf_input_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pfile = tmp_path / "protocol.json"
    pfile.write_bytes(json.dumps(protocol(), indent=2).replace("\n", "\r\n").encode())
    rfile = tmp_path / "record.json"
    rfile.write_bytes(json.dumps(record_body(), indent=2).replace("\n", "\r\n").encode() + b"\r\n")
    store = str(tmp_path / "s")
    os.environ["PROTOCOLITH_NOW"] = ts(0)
    try:
        assert main(["freeze", str(pfile), "--store", store]) == 0
        assert main(["record", str(rfile), "--store", store]) == 0
        assert main(["verify-ledger", "--store", store]) == 0
    finally:
        del os.environ["PROTOCOLITH_NOW"]
    capsys.readouterr()
    ledger = (Path(store) / "ledger.jsonl").read_bytes()
    assert b"\r" not in ledger  # the ledger itself is always LF
    bom = tmp_path / "bom.json"
    bom.write_bytes(b"\xef\xbb\xbf" + json.dumps(protocol()).encode())
    assert main(["freeze", str(bom), "--store", store]) == 2


@pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0), reason="needs POSIX permissions and a non-root user")
def test_read_only_store_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = Store(tmp_path / "s")
    freeze(store, protocol(), clock=clock_at(0))
    record(store, record_body(), clock=clock_at(1))
    before = store.ledger_path.read_bytes()
    for path in (store.path / "lock", store.ledger_path):
        path.chmod(0o444)
    store.path.chmod(0o555)
    try:
        assert verify(store).ok and len(entries(store)) == 2  # readers need no write access
        assert main(["verify-ledger", "--store", str(store.path)]) == 0
        for attempt in (
            lambda: deviation(store, deviation_body(), clock=clock_at(2)),
            lambda: freeze(store, protocol(version="2"), clock=clock_at(2)),
            lambda: issue(store, 1, clock=clock_at(2)),
        ):
            with pytest.raises((EnvError, VerificationFailed, InputError)) as info:
                attempt()
            assert isinstance(info.value, EnvError) and info.value.code == "IO_ERROR"
        capsys.readouterr()
        assert main(["head", "--store", str(store.path)]) == 0
    finally:
        store.path.chmod(0o755)
        for path in (store.path / "lock", store.ledger_path):
            path.chmod(0o644)
    assert store.ledger_path.read_bytes() == before


def test_missing_and_non_directory_store(tmp_path: Path) -> None:
    with pytest.raises(EnvError) as info:
        verify(Store(tmp_path / "absent"))
    assert info.value.code == "NO_LEDGER"
    afile = tmp_path / "file"
    afile.write_text("x")
    with pytest.raises(EnvError) as env:
        freeze(Store(afile), protocol(), clock=clock_at(0))
    assert env.value.code == "IO_ERROR"
    with pytest.raises(EnvError):
        verify(Store(afile))
