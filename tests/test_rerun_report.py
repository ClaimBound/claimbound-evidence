# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

import pytest

from claimbound_evidence.cli import main
from claimbound_evidence.rerun_report import (
    REPRODUCTION_STATUSES,
    build_report,
    classify_hashes,
    suggest_status,
    validate_report,
)
from claimbound_evidence.run_root import RunRootRequest, prepare_run_root


def test_classify_hashes() -> None:
    result = classify_hashes({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "9", "d": "4"})
    assert result["drift"] == "SOURCE_BYTE_DRIFT"
    assert result["files"] == {
        "a": "NO_DRIFT",
        "b": "SOURCE_BYTE_DRIFT",
        "c": "MISSING_RERUN",
        "d": "MISSING_ORIGINAL",
    }
    assert classify_hashes({"a": "1"}, {"a": "1"})["drift"] == "NO_DRIFT"


def test_suggest_status() -> None:
    assert suggest_status(True, "NO_DRIFT") == "REPRODUCED"
    assert suggest_status(True, "SOURCE_BYTE_DRIFT") == "SOURCE_DRIFT"
    assert suggest_status(False, "NO_DRIFT") == "NOT_REPRODUCED"
    assert suggest_status(None, "NO_DRIFT") == "NOT_RERUN"
    assert suggest_status(True, "NO_DRIFT", blocked=True) == "BLOCKED_SOURCE"


def test_validate_report_rejects_unknown_values() -> None:
    assert validate_report({}) == []
    assert validate_report({"reproduction_status": "WIN"})
    assert validate_report({"source_drift": {"drift": "MAYBE"}})
    assert "PARTIALLY_REPRODUCED" in REPRODUCTION_STATUSES
    assert build_report({"a": "1"}, {"a": "1"}, outcome_matches=True)["card_modified"] is False


def test_cli_rerun_report_leaves_inputs_untouched(tmp_path) -> None:
    orig = tmp_path / "orig.json"
    new = tmp_path / "new.json"
    orig.write_text(json.dumps({"a": "1"}), encoding="utf-8")
    new.write_text(json.dumps({"a": "2"}), encoding="utf-8")
    before = orig.read_bytes()
    out = tmp_path / "report.json"
    code = main(
        [
            "rerun", "report", "--original", str(orig), "--rerun", str(new),
            "--outcome", "matches", "--out", str(out),
        ]
    )
    assert code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["reproduction_status"] == "SOURCE_DRIFT"
    assert orig.read_bytes() == before


def test_cli_deviation_roundtrip(tmp_path, capsys) -> None:
    run_dir = prepare_run_root(
        RunRootRequest(protocol_id="p", operator="o", source_url="u", root=tmp_path)
    )[0]
    add = [
        "run-root", "deviation", "add", "--run-dir", str(run_dir), "--step", "s",
        "--planned", "p", "--happened", "h", "--reason", "r", "--who", "w",
    ]
    assert main(add) == 0
    assert main(["run-root", "deviation", "list", "--run-dir", str(run_dir)]) == 0
    assert "deviations=1" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["run-root"])
