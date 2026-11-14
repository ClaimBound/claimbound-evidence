# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from protocolith.cli import main
from protocolith.doctor import run_doctor


def test_run_doctor_passes_for_repo_root() -> None:
    from protocolith import cli

    report = run_doctor(cli.REPO_ROOT)
    assert report.ok
    assert report.checks[0].name == "python"
    assert report.checks[0].ok
    assert report.runs_root.name == "protocolith_runs"


def test_cli_doctor_exits_zero() -> None:
    assert main(["doctor"]) == 0