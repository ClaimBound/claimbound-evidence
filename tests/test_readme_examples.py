# SPDX-License-Identifier: Apache-2.0
"""Run the README quickstart and Python snippet exactly as documented."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
QUICKSTART = REPO_ROOT / "examples" / "quickstart"
README = REPO_ROOT / "README.md"
FILES = ("protocol.json", "record.json", "results.txt")


def _cli() -> list[str]:
    """The ``protocolith`` executable of the active environment, else the module entry point."""
    found = shutil.which("protocolith", path=str(Path(sys.executable).parent))
    if found:
        return [found]
    return [sys.executable, "-c", "import sys; from protocolith.cli import main; sys.exit(main())"]


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    work = tmp_path / "demo"
    work.mkdir()
    for name in FILES:
        shutil.copy(QUICKSTART / name, work / name)
    return work


def _env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("PROTOCOLITH_")}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run(work: Path, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    done = subprocess.run(
        [*_cli(), *args], cwd=work, env=_env(), capture_output=True, text=True, encoding="utf-8", timeout=120
    )
    assert done.returncode == expect, f"{args}: rc={done.returncode}\n{done.stdout}\n{done.stderr}"
    return done


def test_readme_names_the_commands_that_are_tested() -> None:
    text = README.read_text(encoding="utf-8")
    for command in (
        "protocolith freeze protocol.json",
        "protocolith record record.json",
        "protocolith verify-ledger",
        "protocolith issue 1",
        "protocolith log",
        "protocolith head",
    ):
        assert command in text, command


def test_quickstart_record_names_the_hash_of_the_protocol() -> None:
    from protocolith import core

    protocol = core.decode((QUICKSTART / "protocol.json").read_bytes())
    record = json.loads((QUICKSTART / "record.json").read_text(encoding="utf-8"))
    results = (QUICKSTART / "results.txt").read_bytes()
    import hashlib

    assert record["protocol_sha256"] == core.sha256_hex(protocol)
    digest = hashlib.sha256(results).hexdigest()
    assert record["sources"][0]["sha256"] == digest
    assert record["card"]["sanitized_report_sha256"] == digest


def test_quickstart_cli_steps(workdir: Path) -> None:
    frozen = run(workdir, "freeze", "protocol.json").stdout
    assert re.fullmatch(r"frozen QUICKSTART_D001 1 seq=0 hash=[0-9a-f]{64} protocol_sha256=[0-9a-f]{64}\n", frozen)

    recorded = run(workdir, "record", "record.json").stdout
    assert re.fullmatch(r"recorded run-1 PASSED_UNDER_PROTOCOL seq=1 hash=[0-9a-f]{64}\n", recorded)

    assert re.fullmatch(r"OK entries=2 head seq=1 hash=[0-9a-f]{64}\n", run(workdir, "verify-ledger").stdout)

    issued = run(workdir, "issue", "1").stdout.splitlines()
    assert re.fullmatch(r"issued record seq=1 card_sha256=[0-9a-f]{64}", issued[0])
    cards = sorted((workdir / ".protocolith" / "cards").glob("PLITH-QUICKSTART_D001-*"))
    assert [c.suffix for c in cards] == [".json", ".svg"]
    card = json.loads(cards[0].read_text(encoding="utf-8"))
    assert card["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert card["raw_payload_committed"] is False

    verified = run(workdir, "verify-ledger").stdout
    assert verified.startswith("OK entries=3 head seq=2 hash=")

    lines = run(workdir, "log").stdout.splitlines()
    assert [line.split()[1] for line in lines] == ["freeze", "record", "issue"]
    assert lines[0].endswith("QUICKSTART_D001 1")
    assert lines[1].endswith("run-1 PASSED_UNDER_PROTOCOL")
    assert lines[2].endswith("record_seq=1")

    head = run(workdir, "head").stdout
    assert head == f"seq=2 hash={verified.split('hash=')[1]}"
    assert json.loads(run(workdir, "head", "--json").stdout)["seq"] == 2


def test_readme_tamper_claim_exit_code_1(workdir: Path) -> None:
    run(workdir, "freeze", "protocol.json")
    run(workdir, "record", "record.json")
    ledger = workdir / ".protocolith" / "ledger.jsonl"
    ledger.write_bytes(ledger.read_bytes().replace(b"PASSED_UNDER_PROTOCOL", b"NEGATIVE_RESULT_UNDER_PROTOCOL", 1))
    failed = run(workdir, "verify-ledger", expect=1)
    assert "BAD_HASH" in failed.stderr
    assert failed.stdout.startswith("FAILED:")


def test_readme_python_snippet(workdir: Path) -> None:
    text = README.read_text(encoding="utf-8")
    block = re.search(r"```python\n(from pathlib import Path.*?)```", text, re.S)
    assert block, "Python snippet not found in README"
    code = block.group(1)
    script = workdir / "snippet.py"
    script.write_text(code + "\nassert verdict.ok and verdict.count == 2\n", encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(script)], cwd=workdir, env=_env(), capture_output=True, text=True, timeout=120
    )
    assert done.returncode == 0, done.stderr
    lines = done.stdout.splitlines()
    assert lines[0] == "True 2"
    assert lines[1].endswith(".json")
    assert "'count': 3" in lines[2]
    run(workdir, "verify-ledger")


def test_readme_mcp_tool_names(workdir: Path) -> None:
    text = README.read_text(encoding="utf-8")
    requests = "\n".join(
        json.dumps(message)
        for message in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
    )
    done = subprocess.run(
        [*_cli(), "mcp", "--store", str(workdir / ".protocolith")],
        cwd=workdir, env=_env(), input=requests + "\n", capture_output=True, text=True, timeout=120,
    )
    assert done.returncode == 0, done.stderr
    replies = [json.loads(line) for line in done.stdout.splitlines()]
    names = [tool["name"] for tool in replies[1]["result"]["tools"]]
    assert len(names) == 15
    for name in names:
        assert name in text
    config = re.search(r"```json\n(\{\n  \"mcpServers\".*?)```", text, re.S)
    assert config
    server = json.loads(config.group(1))["mcpServers"]["protocolith"]
    assert server["command"] == "protocolith" and server["args"][0] == "mcp"


def test_documented_expect_head_check(workdir: Path) -> None:
    run(workdir, "freeze", "protocol.json")
    run(workdir, "record", "record.json")
    head = json.loads(run(workdir, "head", "--json").stdout)
    anchor = f"{head['seq']}:{head['hash']}"
    assert run(workdir, "verify-ledger", "--expect-head", anchor).stdout.startswith("OK entries=2")
    run(workdir, "issue", "1")
    assert run(workdir, "verify-ledger", "--expect-head", anchor).stdout.startswith("OK entries=3")
    failed = run(workdir, "verify-ledger", "--expect-head", f"1:{'a' * 64}", expect=1)
    assert "HEAD_MISMATCH" in failed.stderr
    run(workdir, "verify-ledger", "--expect-head", "bad", expect=2)
