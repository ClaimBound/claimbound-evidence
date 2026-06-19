# SPDX-License-Identifier: Apache-2.0
"""Cross-platform environment checks for ClaimBound operators."""

from __future__ import annotations

import platform
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


MIN_PYTHON = (3, 12)


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[DoctorCheck, ...]
    platform_system: str
    platform_release: str
    python_version: str
    repo_root: Path
    runs_root: Path
    today_iso: str

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)


def run_doctor(repo_root: Path) -> DoctorReport:
    checks: list[DoctorCheck] = []

    py_ok = sys.version_info[:2] >= MIN_PYTHON
    checks.append(
        DoctorCheck(
            name="python",
            ok=py_ok,
            detail=(
                f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                if py_ok
                else (
                    f"{sys.version_info.major}.{sys.version_info.minor} "
                    f"(need >={MIN_PYTHON[0]}.{MIN_PYTHON[1]})"
                )
            ),
        )
    )

    git_path = shutil.which("git")
    checks.append(
        DoctorCheck(
            name="git",
            ok=git_path is not None,
            detail=git_path or "not found in PATH (required for clone and grok demo)",
        )
    )

    uv_path = shutil.which("uv")
    checks.append(
        DoctorCheck(
            name="uv",
            ok=True,
            detail=(
                uv_path
                if uv_path
                else "not found (optional; pip install -e . also works)"
            ),
        )
    )

    cards_dir = repo_root / "docs" / "evidence_cards"
    registry = repo_root / "docs" / "registry" / "evidence_index.json"
    repo_ok = cards_dir.is_dir() and registry.is_file()
    checks.append(
        DoctorCheck(
            name="repo_layout",
            ok=repo_ok,
            detail=(
                "evidence cards and registry present"
                if repo_ok
                else "missing docs/evidence_cards or docs/registry/evidence_index.json"
            ),
        )
    )

    return DoctorReport(
        checks=tuple(checks),
        platform_system=platform.system(),
        platform_release=platform.release(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        repo_root=repo_root.resolve(),
        runs_root=Path.home() / "claimbound_runs",
        today_iso=date.today().isoformat(),
    )


def format_doctor_report(report: DoctorReport) -> str:
    lines = [
        f"platform={report.platform_system} {report.platform_release}",
        f"python={report.python_version}",
        f"repo_root={report.repo_root.as_posix()}",
        f"runs_root={report.runs_root.as_posix()}",
        f"today={report.today_iso}",
    ]
    for check in report.checks:
        status = "ok" if check.ok else "FAIL"
        lines.append(f"{check.name}={status} ({check.detail})")
    lines.append(f"ready={'yes' if report.ok else 'no'}")
    return "\n".join(lines)