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