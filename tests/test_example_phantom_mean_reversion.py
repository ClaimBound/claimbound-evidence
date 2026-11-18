"""The committed phantom-mean-reversion example verifies and (with numpy) reproduces byte for byte."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "phantom_mean_reversion"
RUNNER = "import sys; from protocolith.cli import main; sys.exit(main())"


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-c", RUNNER, *args], cwd=EXAMPLE, capture_output=True, text=True, check=False)


def test_committed_ledger_verifies_with_anchors() -> None:
    proc = cli("verify-ledger", "--anchors", "--store", "evidence/.protocolith")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "anchors=2" in proc.stdout


def test_record_hashes_match_the_files() -> None:
    record = json.loads((EXAMPLE / "evidence" / "record.json").read_text(encoding="utf-8"))
    for source in record["sources"]:
        assert hashlib.sha256((EXAMPLE / source["id"]).read_bytes()).hexdigest() == source["sha256"], source["id"]


def test_claim_check_is_honest() -> None:
    proc = cli("claim-check", "--seq", "1", "--store", "evidence/.protocolith", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert '"independent_reproduction":false' in proc.stdout.replace(" ", "")


@pytest.mark.skipif(importlib.util.find_spec("numpy") is None, reason="numpy not installed")
def test_results_reproduce_byte_for_byte() -> None:
    proc = subprocess.run([sys.executable, str(EXAMPLE / "reproduce.py")], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
