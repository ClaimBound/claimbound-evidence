from __future__ import annotations

from claimbound_public_benchmarks.run_root import (
    RUN_ROOT_SUBDIRS,
    RunRootRequest,
    prepare_run_root,
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
