# SPDX-License-Identifier: Apache-2.0
"""Tests for ClaimBound track scaffolding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claimbound_evidence.family_ledger import validate_family_ledger
from claimbound_evidence.scaffold import ScaffoldRequest, build_scaffold
from claimbound_evidence.tree_overlay import validate_tree_overlay


def test_scaffold_creates_draft_without_result_status(tmp_path: Path) -> None:
    request = ScaffoldRequest(
        source_url="https://example.org/source",
        protocol_id="EXAMPLE_D001",
        domain="example-domain",
        track_type="source_audit",
        execution_mode="MANUAL_NO_AI",
        out_dir=tmp_path / "docs" / "manual_audit" / "EXAMPLE_D001",
        source_name="Example public source",
        audience="Example audience",
    )

    paths = build_scaffold(request, tmp_path)

    rel_paths = {path.relative_to(tmp_path).as_posix() for path in paths}
    assert rel_paths == {
        "docs/protocols/EXAMPLE_D001_PREREG_CHARTER.md",
        "docs/evidence_requests/EXAMPLE_D001_REQUEST.md",
        "docs/manual_audit/EXAMPLE_D001/EXAMPLE_D001_PLAYBOOK.md",
        "docs/manual_audit/EXAMPLE_D001/EXAMPLE_D001_CHECKLIST.md",
        "docs/manual_audit/EXAMPLE_D001/EXAMPLE_D001_OPERATOR_DECLARATION.md",
        "docs/evidence_card_drafts/CLAIMBOUND-EXAMPLE_D001-DRAFT.json",
        "docs/registry_patch_drafts/EXAMPLE_D001_REGISTRY_PATCH.json",
        "docs/track_families/EXAMPLE_D001_FAMILY_LEDGER.json",
        "docs/track_families/EXAMPLE_D001_TREE.json",
        "artifacts/example_d001_source_probe_summary.json",
    }

    card = json.loads(
        (tmp_path / "docs/evidence_card_drafts/CLAIMBOUND-EXAMPLE_D001-DRAFT.json").read_text(
            encoding="utf-8"
        )
    )
    assert card["draft_status"] == "GRAY_DRAFT_NOT_EXECUTED"
    assert card["raw_payload_committed"] is False
    assert "result_status" not in card
    assert "PASSED_UNDER_PROTOCOL" not in json.dumps(card)

    probe = json.loads(
        (tmp_path / "artifacts/example_d001_source_probe_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert probe["network_fetch_performed"] is False
    assert probe["claim_boundary"]

    ledger = json.loads(
        (tmp_path / "docs/track_families/EXAMPLE_D001_FAMILY_LEDGER.json").read_text(
            encoding="utf-8"
        )
    )
    assert validate_family_ledger(ledger) == []
    assert ledger["track_budget"]["max_proof_tracks_per_hypothesis"] == 3

    tree = json.loads(
        (tmp_path / "docs/track_families/EXAMPLE_D001_TREE.json").read_text(
            encoding="utf-8"
        )
    )
    assert tree["protocol_version"] == "claimbound-tree-v3"
    assert validate_tree_overlay(tree) == []


def _req(tmp_path: Path, **kw: object) -> ScaffoldRequest:
    base: dict[str, object] = {
        "source_url": "https://example.org/source",
        "protocol_id": "EXAMPLE_D002",
        "domain": "d",
        "track_type": "source_audit",
        "execution_mode": "MANUAL_NO_AI",
        "out_dir": tmp_path / "docs" / "manual_audit" / "X",
        "source_name": "n",
        "audience": "a",
        "created_at": "2026-01-02",
    }
    base.update(kw)
    return ScaffoldRequest(**base)  # type: ignore[arg-type]


def test_gray_markers_everywhere(tmp_path: Path) -> None:
    paths = build_scaffold(_req(tmp_path), tmp_path)
    for path in paths:
        if path.name.endswith(("_source_probe_summary.json", "_FAMILY_LEDGER.json", "_TREE.json")):
            continue
        assert "NOT_EVIDENCE" in path.read_text(encoding="utf-8"), path.name
    patch = json.loads(next(p for p in paths if "REGISTRY_PATCH" in p.name).read_text(encoding="utf-8"))
    assert patch["patch_status"] == "GRAY_DRAFT_NOT_EVIDENCE"
    assert patch["entry"] == "NOT_CREATED_YET"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    paths = build_scaffold(_req(tmp_path), tmp_path, dry_run=True)
    assert len(paths) == 10
    assert not any(tmp_path.iterdir())


def test_refuses_overwrite_atomically(tmp_path: Path) -> None:
    req = _req(tmp_path)
    existing = tmp_path / "docs" / "evidence_requests" / "EXAMPLE_D002_REQUEST.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        build_scaffold(req, tmp_path)
    assert existing.read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / "docs" / "protocols").exists()


def test_refuses_symlink_escape(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "docs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        build_scaffold(_req(tmp_path, out_dir=repo / "out"), repo)
    assert not any(outside.iterdir())


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "ftp://x.org/a", "javascript:alert(1)", "https://", "example.org", "https://a.org/x y"],
)
def test_rejects_bad_urls(tmp_path: Path, url: str) -> None:
    with pytest.raises(ValueError):
        build_scaffold(_req(tmp_path, source_url=url), tmp_path, dry_run=True)


@pytest.mark.parametrize("pid", ["", "ab", "../evil", "A/B", "x" * 80, "A.B", "-ab"])
def test_rejects_bad_protocol_ids(tmp_path: Path, pid: str) -> None:
    with pytest.raises(ValueError):
        build_scaffold(_req(tmp_path, protocol_id=pid), tmp_path, dry_run=True)


def test_output_is_deterministic(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    pa = build_scaffold(_req(a, out_dir=a / "o"), a)
    pb = build_scaffold(_req(b, out_dir=b / "o"), b)
    assert [p.relative_to(a).as_posix() for p in pa] == [p.relative_to(b).as_posix() for p in pb]
    for x, y in zip(pa, pb, strict=True):
        assert x.read_bytes() == y.read_bytes()


def test_bad_created_at_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="created_at"):
        build_scaffold(_req(tmp_path, created_at="yesterday"), tmp_path, dry_run=True)
