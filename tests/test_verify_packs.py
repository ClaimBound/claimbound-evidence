# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from claimbound_evidence.cli import main
from claimbound_evidence.verify_packs import (
    run_verify_pack,
    verify_source_probe_spec,
    verify_static_registry_spec,
)


def test_verify_source_probe_spec_passes() -> None:
    from claimbound_evidence import cli

    checks = verify_source_probe_spec(cli.REPO_ROOT)
    assert all(check.ok for check in checks)


def test_verify_static_registry_spec_passes() -> None:
    from claimbound_evidence import cli

    checks = verify_static_registry_spec(cli.REPO_ROOT)
    assert all(check.ok for check in checks)


def test_cli_verify_api_parity() -> None:
    assert main(["verify", "api-parity"]) == 0


def test_cli_verify_ai_boundary() -> None:
    assert main(["verify", "ai-boundary"]) == 0


def test_verify_eea_drift_offline(monkeypatch) -> None:
    from claimbound_evidence import cli
    from claimbound_evidence.verify_packs import verify_eea_drift

    monkeypatch.setattr(
        "claimbound_evidence.workflows.drift_eea_source_audit",
        lambda repo_root, **kwargs: 0,
    )
    checks = verify_eea_drift(cli.REPO_ROOT)
    assert all(check.ok for check in checks)


def test_verify_pack_names_include_tier_bc() -> None:
    from claimbound_evidence.verify_packs import VERIFY_PACKS

    assert "eea-drift" in VERIFY_PACKS
    assert "nasa-rerun" in VERIFY_PACKS
    assert "noaa-rerun" in VERIFY_PACKS