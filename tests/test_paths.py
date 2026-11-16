"""Tests for the home directory helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from protocolith._paths import home_dir


def test_home_dir_uses_the_home_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert home_dir() == tmp_path


def test_home_dir_falls_back_to_the_temporary_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(cls: type[Path]) -> Path:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(Path, "home", classmethod(boom))
    assert home_dir() == Path(__import__("tempfile").gettempdir())


def test_cli_imports_without_a_home_directory() -> None:
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parent.parent
    env = {"PYTHONPATH": str(root / "src"), **{k: v for k, v in os.environ.items() if k in ("SYSTEMROOT", "TEMP", "TMP", "TMPDIR")}}
    proc = subprocess.run(
        [sys.executable, "-I", "-c", "import protocolith.cli as c; c.build_parser()"], capture_output=True, text=True, env=env, check=False
    )
    assert proc.returncode == 0, proc.stderr
