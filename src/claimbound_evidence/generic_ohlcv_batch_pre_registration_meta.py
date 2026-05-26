# SPDX-License-Identifier: Apache-2.0

"""Sanitization and reproducibility helpers for generic OHLCV non-spec batch JSON."""

from __future__ import annotations

from pathlib import Path

_DOMAIN_LABEL_MAX_LEN = 120
_OPERATOR_NOTES_MAX_LEN = 500
_DATASET_ID_MAX_LEN = 200
_DATASET_LICENSE_NOTE_MAX_LEN = 400


def sanitize_domain_label(value: str | None) -> str | None:
    if value is None:
        return None
    s = " ".join(str(value).strip().split())
    if not s:
        return None
    return s[:_DOMAIN_LABEL_MAX_LEN].rstrip()


def sanitize_operator_notes(value: str | None) -> str | None:
    if value is None:
        return None
    s = " ".join(str(value).strip().split())
    if not s:
        return None
    return s[:_OPERATOR_NOTES_MAX_LEN].rstrip()


def sanitize_dataset_id(value: str | None) -> str | None:
    if value is None:
        return None
    s = " ".join(str(value).strip().split())
    if not s:
        return None
    return s[:_DATASET_ID_MAX_LEN].rstrip()


def sanitize_dataset_license_note(value: str | None) -> str | None:
    if value is None:
        return None
    s = " ".join(str(value).strip().split())
    if not s:
        return None
    return s[:_DATASET_LICENSE_NOTE_MAX_LEN].rstrip()


def build_dataset_contract_v1(
    dataset_id: str | None,
    dataset_license_note: str | None,
) -> dict[str, str] | None:
    """Phase 2 hook: frozen dataset identity in pre_registration; does not affect scoring."""

    sid = sanitize_dataset_id(dataset_id)
    lic = sanitize_dataset_license_note(dataset_license_note)
    if sid is None and lic is None:
        return None
    out: dict[str, str] = {"schema": "dataset_contract_v1"}
    if sid is not None:
        out["dataset_id"] = sid
    if lic is not None:
        out["license_note"] = lic
    return out


def _find_repo_root_with_version_manifest(start: Path) -> Path | None:
    for p in (start, *start.parents):
        if (p / "specs" / "repo_version.yaml").is_file():
            return p
    return None


def _read_repo_semver_from_manifest(repo_root: Path) -> str | None:
    path = repo_root / "specs" / "repo_version.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("repo_semver:"):
            return stripped.split(":", 1)[1].strip()
    return None


def _git_head_short(repo_root: Path) -> str | None:
    import subprocess

    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out[:40] if out else None


def build_generic_ohlcv_batch_reproducibility() -> dict[str, object]:
    """Release manifest hooks for the public release without changing scoring."""

    root = _find_repo_root_with_version_manifest(Path(__file__).resolve().parent)
    if root is None:
        return {
            "schema": "generic_ohlcv_batch_reproducibility_v1",
            "repo_semver": None,
            "git_commit_short": None,
        }
    return {
        "schema": "generic_ohlcv_batch_reproducibility_v1",
        "repo_semver": _read_repo_semver_from_manifest(root),
        "git_commit_short": _git_head_short(root),
    }
