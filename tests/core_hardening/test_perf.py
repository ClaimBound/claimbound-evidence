# SPDX-License-Identifier: Apache-2.0
"""CPU-time measurements (``time.process_time``), run with ``-m perf``.

Budgets are generous (at least 5x slack over a quiet machine) so a shared or loaded machine does not fail them; the
numbers themselves are indicative only. Set ``PROTOCOLITH_PERF_JSON`` to a path to dump them as JSON.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from hardening_support import clock_at, deviation_body, fast_ledger, protocol, record_body

from protocolith.core import Store, decode, deviation, encode, freeze, log, scan, sha256_hex, summary, verify
from protocolith.core.issue import card_hash

pytestmark = pytest.mark.perf
RESULTS: dict[str, Any] = {}


def cpu(work: Callable[[], Any], repeat: int = 1) -> float:
    """CPU seconds of the best of ``repeat`` runs."""
    best = float("inf")
    for _ in range(repeat):
        start = time.process_time()
        work()
        best = min(best, time.process_time() - start)
    return best


@pytest.fixture(scope="module", autouse=True)
def _dump_results() -> Any:
    yield
    target = os.environ.get("PROTOCOLITH_PERF_JSON")
    if target:
        Path(target).write_text(json.dumps(RESULTS, indent=1, sort_keys=True) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def ledger_10k() -> bytes:
    return fast_ledger(10_000)


def test_canonicalization_throughput() -> None:
    value = {"body": record_body(), "seq": 1, "ts": "2026-11-15T10:00:00Z", "type": "record", "v": 1}
    n = 5_000
    text = encode(value)
    enc = cpu(lambda: [encode(value) for _ in range(n)], repeat=3)
    dec = cpu(lambda: [decode(text) for _ in range(n)], repeat=3)
    sha = cpu(lambda: [sha256_hex(value) for _ in range(n)], repeat=3)
    RESULTS["canonicalization"] = {
        "entry_bytes": len(text),
        "encode_per_s": round(n / enc),
        "decode_per_s": round(n / dec),
        "sha256_hex_per_s": round(n / sha),
    }
    assert enc < 5.0 and dec < 5.0 and sha < 5.0  # about 0.1 s each on a quiet machine


def test_verify_throughput_and_linearity(ledger_10k: bytes, tmp_path: Path) -> None:
    half = b"".join(ledger_10k.splitlines(keepends=True)[:5_000])
    assert scan(half, card_hash)[0].count == 5_000
    t_half = cpu(lambda: scan(half, card_hash), repeat=3)
    t_full = cpu(lambda: scan(ledger_10k, card_hash), repeat=3)
    store = Store(tmp_path / "s")
    store.path.mkdir()
    store.ledger_path.write_bytes(ledger_10k)
    t_file = cpu(lambda: verify(store))
    assert verify(store).ok
    RESULTS["verify"] = {
        "entries": 10_000,
        "ledger_bytes": len(ledger_10k),
        "scan_10k_cpu_s": round(t_full, 3),
        "scan_5k_cpu_s": round(t_half, 3),
        "ratio_10k_over_5k": round(t_full / t_half, 2),
        "entries_per_s": round(10_000 / t_full),
        "verify_from_file_10k_cpu_s": round(t_file, 3),
    }
    assert t_full < 30.0 and t_file < 30.0  # about 0.6 s on a quiet machine
    assert t_full / t_half < 3.0, "verification time must scale roughly linearly"


def test_summary_and_filtered_log_on_10k_entries(ledger_10k: bytes, tmp_path: Path) -> None:
    store = Store(tmp_path / "s")
    store.path.mkdir()
    store.ledger_path.write_bytes(ledger_10k)
    t_verify = cpu(lambda: verify(store), repeat=3)
    t_summary = cpu(lambda: summary(store), repeat=3)
    t_log = cpu(lambda: log(store, type="deviation", tail=20), repeat=3)
    found = summary(store)
    assert found["ok"] and found["head"]["count"] == 10_000 and len(log(store, type="deviation", tail=20)) == 20
    RESULTS["summary"] = {
        "entries": 10_000,
        "verify_cpu_s": round(t_verify, 3),
        "summary_cpu_s": round(t_summary, 3),
        "filtered_log_cpu_s": round(t_log, 3),
    }
    assert t_summary < 5.0 and t_log < 5.0  # well under 1 s on a quiet machine; summary costs about one verification


def test_append_throughput(tmp_path: Path) -> None:
    store = Store(tmp_path / "s")
    freeze(store, protocol(), clock=clock_at(0))

    def appends(count: int, offset: int) -> None:
        for i in range(count):
            deviation(store, deviation_body(description=f"d{offset + i}"), clock=clock_at(1))

    small = cpu(lambda: appends(100, 0))  # ledger grows 1 -> 101 entries
    appends(800, 100)  # ledger now about 900 entries
    large = cpu(lambda: appends(100, 900))  # ledger grows 901 -> 1001 entries
    assert verify(store).count == 1001
    RESULTS["append"] = {
        "appends_per_s_ledger_1_to_101": round(100 / small),
        "appends_per_s_ledger_901_to_1001": round(100 / large),
        "cpu_per_append_ms_at_100_entries": round(1000 * small / 100, 3),
        "cpu_per_append_ms_at_1000_entries": round(1000 * large / 100, 3),
        "note": "each append re-verifies the whole ledger under the lock, so its cost grows linearly with ledger size; "
        "CPU time excludes time blocked in fsync",
    }
    assert small < 10.0 and large < 60.0
    assert large / small < 30.0  # about 10x for 10x the entries; 30x would mean worse than linear growth


def test_verify_with_anchors_costs_about_the_same_on_10k_entries(ledger_10k: bytes, tmp_path: Path) -> None:
    from protocolith.core import anchor_head

    store = Store(tmp_path / "s")
    store.path.mkdir()
    store.ledger_path.write_bytes(ledger_10k)
    for cut in (2_000, 6_000, 10_000):  # three anchors at different heads
        full = store.ledger_path.read_bytes()
        store.ledger_path.write_bytes(b"".join(ledger_10k.splitlines(keepends=True)[:cut]))
        anchor_head(store, clock=clock_at(1))
        store.ledger_path.write_bytes(full)
    assert verify(store, anchors=True).ok and verify(store, anchors=True).anchors == 3
    plain = cpu(lambda: verify(store), repeat=3)
    anchored = cpu(lambda: verify(store, anchors=True), repeat=3)
    RESULTS["verify_anchors"] = {"entries": 10_000, "anchors": 3, "plain_cpu_s": round(plain, 3), "anchored_cpu_s": round(anchored, 3)}
    assert anchored < plain * 1.5 + 0.05, "anchor checks must not dominate verification"
