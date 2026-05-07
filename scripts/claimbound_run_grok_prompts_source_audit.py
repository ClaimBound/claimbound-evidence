#!/usr/bin/env python3
"""Audit a local clone of xai-org/grok-prompts without committing prompt text."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


PROMPT_SUFFIXES = {".j2", ".txt"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo_dir: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_dir), *args],
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def build_report(repo_dir: Path) -> dict[str, object]:
    if not repo_dir.exists():
        raise FileNotFoundError(repo_dir)

    head_commit = _git(repo_dir, "rev-parse", "HEAD")
    remote_url = _git(repo_dir, "config", "--get", "remote.origin.url")
    files = sorted(
        path
        for path in repo_dir.iterdir()
        if path.is_file() and path.suffix.lower() in PROMPT_SUFFIXES
    )

    required = [repo_dir / "README.md", repo_dir / "LICENSE"]
    missing_required = [path.name for path in required if not path.is_file()]

    prompt_manifest = [
        {
            "path": path.name,
            "sha256": _sha256(path),
            "byte_size": path.stat().st_size,
        }
        for path in files
    ]

    normalized_remote = remote_url.removesuffix(".git")

    pass_gate = (
        normalized_remote == "https://github.com/xai-org/grok-prompts"
        and head_commit != ""
        and missing_required == []
        and len(prompt_manifest) >= 1
    )

    return {
        "protocol_id": "GROK_PROMPTS_SOURCE_AUDIT_D001",
        "record_type": "source_audit",
        "result_status": "PASSED_UNDER_PROTOCOL" if pass_gate else "BLOCKED_SOURCE",
        "card_validity_level": "GREEN_VALIDATED" if pass_gate else "RED_INVALID_OR_TAMPER_EVIDENCE",
        "official_source_name": "xAI Grok prompts GitHub repository",
        "official_source_url": "https://github.com/xai-org/grok-prompts",
        "remote_url": remote_url,
        "head_commit": head_commit,
        "license_file_present": (repo_dir / "LICENSE").is_file(),
        "readme_file_present": (repo_dir / "README.md").is_file(),
        "missing_required_files": missing_required,
        "prompt_file_count": len(prompt_manifest),
        "prompt_manifest": prompt_manifest,
        "raw_prompt_text_committed": False,
        "raw_payload_committed": False,
        "raw_payload_policy": "Prompt text is not committed to this repository; only path, byte size and SHA-256 manifest are recorded.",
        "claim_boundary": (
            "This source-audit record verifies public repository availability, "
            "commit identity, license/readme presence and prompt-file hashes only. "
            "It does not prove that any live Grok runtime uses these exact prompts."
        ),
        "known_limitations": [
            "No live Grok runtime equivalence is claimed.",
            "No model quality, safety or benchmark-performance claim is made.",
            "No hidden server-side prompt or policy layer is ruled out.",
        ],
    }


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report(args.repo_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.report.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
