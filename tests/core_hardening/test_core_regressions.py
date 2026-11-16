# SPDX-License-Identifier: Apache-2.0
"""Regression tests for defects found by the hardening campaign, and the --expect-head option.

These tests also keep ``protocolith.core`` at 100% line and branch coverage for the code added here; run them
together with ``tests/core`` (``pytest tests/core tests/core_hardening/test_core_regressions.py --cov=protocolith.core``).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
from hardening_support import PROTOCOL_SHA, clock_at, protocol, record_body

from protocolith.cli import main
from protocolith.core import EnvError, InputError, Store, freeze, head, issue, record, scan, verify
from protocolith.core.errors import io_guard
from protocolith.core.issue import card_hash
from protocolith.core.ledger import ZERO_HASH, make_entry, parse_head_ref, serialize
from protocolith.core.mcp import handle_line

HASH_A = "a" * 64


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "store")


@pytest.fixture
def recorded(store: Store) -> Store:
    """A store with one freeze (seq 0) and one record (seq 1)."""
    freeze(store, protocol(), clock=clock_at(0))
    record(store, record_body(), clock=clock_at(0))
    return store


# --- verify --expect-head -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    ["", "1", "1:", f":{HASH_A}", f"01:{HASH_A}", f"-1:{HASH_A}", f"1:{HASH_A.upper()}", f"1:{HASH_A[:-1]}", f"1:{HASH_A}\n",
     f"1 :{HASH_A}", f"٣:{HASH_A}", 5, None, [1]],
)  # fmt: skip
def test_parse_head_ref_rejects_malformed(bad: Any) -> None:
    with pytest.raises(InputError) as info:
        parse_head_ref(bad)
    assert info.value.code == "BAD_ENTRY"


def test_parse_head_ref_accepts() -> None:
    assert parse_head_ref(f"0:{HASH_A}") == (0, HASH_A)
    assert parse_head_ref(f"12345678901234567890:{HASH_A}") == (12345678901234567890, HASH_A)


def test_expect_head_ok_and_mismatches(recorded: Store) -> None:
    tip = head(recorded)
    assert verify(recorded, f"1:{tip['hash']}").ok
    first = json.loads(recorded.ledger_path.read_bytes().splitlines()[0])["hash"]
    assert verify(recorded, f"0:{first}").ok  # an earlier entry of an intact ledger also matches
    wrong = verify(recorded, f"1:{HASH_A}")
    assert not wrong.ok and wrong.codes == ["HEAD_MISMATCH"] and wrong.violations[0].seq == 1
    swapped = verify(recorded, f"0:{tip['hash']}")
    assert swapped.codes == ["HEAD_MISMATCH"]
    removed = verify(recorded, f"2:{HASH_A}")
    assert removed.codes == ["HEAD_MISMATCH"] and "no entry at seq 2" in removed.violations[0].message
    assert wrong.to_dict()["ok"] is False and wrong.count == 2


def test_expect_head_does_not_mask_other_failures(recorded: Store) -> None:
    recorded.ledger_path.write_bytes(recorded.ledger_path.read_bytes() + b'{"body"')
    assert verify(recorded, f"1:{HASH_A}").codes == ["TRUNCATED_TAIL"]


def test_expect_head_is_validated_before_the_store_is_read(tmp_path: Path) -> None:
    with pytest.raises(InputError) as info:
        verify(Store(tmp_path / "missing"), "nope")
    assert info.value.code == "BAD_ENTRY"
    with pytest.raises(EnvError) as env:
        verify(Store(tmp_path / "missing"), f"0:{HASH_A}")
    assert env.value.code == "NO_LEDGER"


def test_expect_head_cli(recorded: Store, capsys: pytest.CaptureFixture[str]) -> None:
    tip = head(recorded)
    args = ["verify-ledger", "--store", str(recorded.path)]
    assert main([*args, "--expect-head", f"1:{tip['hash']}"]) == 0
    assert capsys.readouterr().out.startswith("OK entries=2")
    assert main([*args, "--expect-head", f"1:{HASH_A}", "--json"]) == 1
    captured = capsys.readouterr()
    assert "HEAD_MISMATCH line 1" in captured.err and json.loads(captured.out)["codes"] == ["HEAD_MISMATCH"]
    assert main([*args, "--expect-head", "garbage"]) == 2
    assert "BAD_ENTRY" in capsys.readouterr().err


def test_expect_head_mcp(recorded: Store) -> None:
    def call(arguments: dict[str, Any]) -> tuple[bool, Any]:
        params = {"name": "protocolith_verify", "arguments": arguments}
        message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}
        reply = handle_line(json.dumps(message).encode(), recorded, clock_at(9))
        assert reply is not None
        result = json.loads(reply)["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    tip = head(recorded)
    assert call({"expect_head": f"1:{tip['hash']}"}) == (False, verify(recorded).to_dict())
    error, data = call({"expect_head": f"1:{HASH_A}"})
    assert error and data["codes"] == ["HEAD_MISMATCH"]
    error, data = call({"expect_head": 7})
    assert error and data["error"]["code"] == "BAD_ENTRY"


# --- defects found by hardening ---------------------------------------------------------------------


def test_card_validator_crash_is_an_input_error(store: Store) -> None:
    """A card field of an unexpected type used to escape as a raw TypeError from the validator."""
    freeze(store, protocol(), clock=clock_at(0))
    record(store, record_body(card={**record_body()["card"], "verification_level": []}), clock=clock_at(1))
    with pytest.raises(InputError) as info:
        issue(store, 1, clock=clock_at(2))
    assert info.value.code == "CARD_INVALID" and "TypeError" in info.value.message


def test_verify_reports_bad_card_instead_of_raising() -> None:
    body = record_body(card={**record_body()["card"], "verification_level": {}})
    freeze_body = {
        "protocol_id": "DEMO_D001", "protocol": protocol(), "protocol_sha256": PROTOCOL_SHA, "supersedes": None, "version": "1",
    }  # fmt: skip
    first = make_entry(seq=0, prev=ZERO_HASH, ts=clock_at(0)(), type="freeze", body=freeze_body)
    second = make_entry(seq=1, prev=first["hash"], ts=clock_at(1)(), type="record", body=body)
    third_body = {"card_sha256": HASH_A, "format": "evidence-card-json-svg", "record_seq": 1}
    third = make_entry(seq=2, prev=second["hash"], ts=clock_at(2)(), type="issue", body=third_body)
    verdict, _ = scan(b"".join(serialize(e) for e in (first, second, third)), card_hash)
    assert verdict.codes == ["BAD_CARD"] and not verdict.ok


def test_svg_never_contains_characters_xml_forbids(store: Store) -> None:
    """Control characters in card text used to make the SVG malformed XML."""
    freeze(store, protocol(), clock=clock_at(0))
    card = {**record_body()["card"], "known_limitations": ["a\x1bb\x00c\ufffed\x0b"]}
    record(store, record_body(card=card), clock=clock_at(1))
    result = issue(store, 1, clock=clock_at(2))
    svg = Path(result["svg_path"]).read_text(encoding="utf-8")
    ET.fromstring(svg)
    assert "a\ufffdb\ufffdc\ufffdd" in svg  # the renderer may trim trailing space
    assert json.loads(Path(result["json_path"]).read_bytes())["known_limitations"] == card["known_limitations"]  # JSON card is verbatim


def test_nul_in_a_path_is_an_environment_error() -> None:
    for call in (lambda: verify(Store("bad\0path")), lambda: freeze(Store("bad\0path"), protocol(), clock=clock_at(0))):
        with pytest.raises(EnvError) as info:
            call()
        assert info.value.code == "IO_ERROR"
    with pytest.raises(ValueError, match="unrelated"), io_guard():
        raise ValueError("unrelated")
