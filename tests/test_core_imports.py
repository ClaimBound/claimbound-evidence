"""The core must import and run without the optional runner and campaign dependencies."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLOCKER = textwrap.dedent(
    """
    import sys

    class _Block:
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in {"numpy", "pdfplumber", "pypdf"}:
                raise ModuleNotFoundError(f"blocked optional dependency {name}", name=name)

    sys.meta_path.insert(0, _Block())
    """
)


def _run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-c", BLOCKER + textwrap.dedent(code)],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
    )


def test_core_modules_import_without_optional_dependencies() -> None:
    proc = _run(
        """
        import protocolith, protocolith.cli, protocolith.evidence_card, protocolith.registry
        import protocolith.family_ledger, protocolith.run_root, protocolith.tree_overlay
        assert "numpy" not in sys.modules
        """
    )
    assert proc.returncode == 0, proc.stderr


def test_core_command_runs_without_optional_dependencies() -> None:
    card = sorted((ROOT / "docs" / "evidence_cards").glob("PLITH-*.json"))[0]
    proc = _run(
        f"""
        from protocolith.cli import main
        raise SystemExit(main(["validate-card", {str(card)!r}]))
        """
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_runner_command_explains_the_missing_extra() -> None:
    proc = _run(
        """
        from protocolith.cli import main
        main(["rerun", "nasa-d103"])
        """
    )
    assert proc.returncode != 0
    assert "protocolith[runners]" in proc.stderr
