# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from claimbound_evidence.cli import main
from claimbound_evidence.inspect import format_hash_lines, hash_files, pick_fields


def test_pick_fields_extracts_subset() -> None:
    data = {"evidence_id": "X", "result_status": "PASSED_UNDER_PROTOCOL", "extra": 1}
    assert pick_fields(data, ("evidence_id", "result_status")) == {
        "evidence_id": "X",
        "result_status": "PASSED_UNDER_PROTOCOL",
    }


def test_hash_files_produces_stable_digest(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text('{"a":1}', encoding="utf-8")
    digest, _ = hash_files((path,))[0]
    assert len(digest) == 64
    assert format_hash_lines([(digest, path)]) == f"{digest}  {path.as_posix()}\n"


def test_cli_inspect_card_flagship(tmp_path: Path, monkeypatch, capsys) -> None:
    from claimbound_evidence import cli

    card = {
        "evidence_id": "CLAIMBOUND-NASA-POWER-D103-2026-04-29",
        "result_status": "PASSED_UNDER_PROTOCOL",
        "reproduction_level": "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT",
        "claim_boundary": "narrow gate",
    }
    path = tmp_path / "card.json"
    path.write_text(json.dumps(card), encoding="utf-8")
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)

    assert (
        main(
            [
                "inspect",
                "card",
                str(path),
                "--keys",
                "evidence_id",
                "result_status",
                "reproduction_level",
                "claim_boundary",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT" in out