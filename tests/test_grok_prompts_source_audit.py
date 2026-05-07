# SPDX-License-Identifier: Apache-2.0
"""Tests for the Grok prompts source audit helper."""

from __future__ import annotations

import importlib.util as ilu
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "claimbound_run_grok_prompts_source_audit.py"


def _load_script():
    spec = ilu.spec_from_file_location("claimbound_run_grok_prompts_source_audit", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grok_prompts_source_audit_passes_on_minimal_repo(tmp_path: Path) -> None:
    repo = tmp_path / "grok-prompts"
    repo.mkdir()
    subprocess.check_call(["git", "-C", str(repo), "init", "-q"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "test@example.org"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "Test"])
    subprocess.check_call(
        ["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/xai-org/grok-prompts.git"]
    )
    (repo / "README.md").write_text("# Grok prompts\n", encoding="utf-8")
    (repo / "LICENSE").write_text("license\n", encoding="utf-8")
    (repo / "prompt.j2").write_text("system prompt template\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", str(repo), "add", "."])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-q", "-m", "fixture"])

    report = _load_script().build_report(repo)

    assert report["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert report["prompt_file_count"] == 1
    assert report["raw_prompt_text_committed"] is False
    assert report["claim_boundary"]
