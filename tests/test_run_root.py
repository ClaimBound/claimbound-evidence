# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from claimbound_evidence.run_root import (
    RUN_ROOT_SUBDIRS,
    RunRootRequest,
    add_deviation,
    list_deviations,
    prepare_run_root,
    record_rights_answer,
)


def test_prepare_run_root_creates_operator_workspace(tmp_path) -> None:
    created = prepare_run_root(
        RunRootRequest(
            protocol_id="example-d001",
            operator="tester",
            source_url="https://example.org/source",
            root=tmp_path,
        )
    )

    run_dir = created[0]
    assert run_dir.is_dir()
    for subdir in RUN_ROOT_SUBDIRS:
        assert (run_dir / subdir).is_dir()

    context = (run_dir / "RUN_CONTEXT.md").read_text(encoding="utf-8")
    deviations = (run_dir / "DEVIATIONS.md").read_text(encoding="utf-8")
    manifest = (run_dir / "LOCAL_MANIFEST.md").read_text(encoding="utf-8")

    assert "EXAMPLE_D001" in context
    assert "Do not commit raw payloads" in context
    assert "Effect on status" in deviations
    assert "SHA-256 or blocked reason" in manifest


def _make(tmp_path):
    return prepare_run_root(
        RunRootRequest(protocol_id="x-1", operator="t", source_url="https://e.org", root=tmp_path)
    )[0]


def test_run_root_has_deviation_jsonl_and_rights_checklist(tmp_path) -> None:
    run_dir = _make(tmp_path)
    assert (run_dir / "deviations.jsonl").read_text(encoding="utf-8") == ""
    rights = (run_dir / "SOURCE_RIGHTS_CHECKLIST.md").read_text(encoding="utf-8")
    assert "not a legal" in rights
    assert "robots" in rights and "redistribution" in rights and "attribution" in rights


def test_deviation_add_list_append_only(tmp_path) -> None:
    run_dir = _make(tmp_path)
    kw = {"step": "fetch", "planned": "a", "happened": "b", "reason": "c", "who": "op"}
    add_deviation(run_dir, **kw)
    add_deviation(run_dir, **{**kw, "step": "score"})
    entries = list_deviations(run_dir)
    assert [e["step"] for e in entries] == ["fetch", "score"]
    assert entries[0]["timestamp"]


def test_deviation_rejects_empty_and_bad_lines(tmp_path) -> None:
    run_dir = _make(tmp_path)
    with pytest.raises(ValueError):
        add_deviation(run_dir, step=" ", planned="a", happened="b", reason="c", who="op")
    (run_dir / "deviations.jsonl").write_text('{"step": "x"}\n', encoding="utf-8")
    with pytest.raises(ValueError):
        list_deviations(run_dir)


def test_rights_answer_recorded(tmp_path) -> None:
    run_dir = _make(tmp_path)
    record_rights_answer(run_dir, "robots", "no disallow for /api", "op")
    assert "no disallow" in (run_dir / "source_rights_answers.jsonl").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        record_rights_answer(run_dir, "bogus", "x", "op")
