# SPDX-License-Identifier: Apache-2.0
"""Local-only run-root helpers for ClaimBound operators."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


RUN_ROOT_SUBDIRS = ("raw", "logs", "hashes", "reports", "transcripts")


@dataclass(frozen=True)
class RunRootRequest:
    protocol_id: str
    operator: str
    source_url: str
    root: Path


def prepare_run_root(request: RunRootRequest) -> list[Path]:
    """Create a local-only ClaimBound run root with standard operator files."""

    protocol_id = _normalize_protocol_id(request.protocol_id)
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_dir = request.root / _run_dir_name(protocol_id)
    run_dir.mkdir(parents=True, exist_ok=False)

    created: list[Path] = [run_dir]
    for subdir in RUN_ROOT_SUBDIRS:
        path = run_dir / subdir
        path.mkdir()
        created.append(path)

    context_path = run_dir / "RUN_CONTEXT.md"
    context_path.write_text(
        _render_run_context(protocol_id, request.operator, request.source_url, created_at),
        encoding="utf-8",
    )
    created.append(context_path)

    deviation_path = run_dir / "DEVIATIONS.md"
    deviation_path.write_text(_render_deviation_log(protocol_id), encoding="utf-8")
    created.append(deviation_path)

    manifest_path = run_dir / "LOCAL_MANIFEST.md"
    manifest_path.write_text(_render_local_manifest(protocol_id), encoding="utf-8")
    created.append(manifest_path)

    return created


def _run_dir_name(protocol_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{protocol_id.lower()}_{stamp}"


def _normalize_protocol_id(protocol_id: str) -> str:
    normalized = protocol_id.strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized:
        raise ValueError("protocol_id must not be empty")
    return normalized


def _render_run_context(
    protocol_id: str, operator: str, source_url: str, created_at: str
) -> str:
    return f"""# ClaimBound Local Run Context

This directory is local-only. Do not commit raw payloads, transcripts, source
downloads or private logs from this run root.

## Run

- Protocol ID: {protocol_id}
- Operator: {operator}
- Source URL: {source_url}
- Created at: {created_at}

## Freeze Checklist

- [ ] I read the protocol before collecting fresh outcomes.
- [ ] Source, target, selection rule, scoring rule and gate are fixed.
- [ ] Stop conditions are written down.
- [ ] Raw payload policy is understood.
- [ ] Broad forbidden claims are listed.

## Output Checklist

- [ ] Raw artifacts stayed outside the public repository.
- [ ] Raw hashes or blocked-hashing reason are recorded.
- [ ] Commands and logs are recorded.
- [ ] Sanitized summary can be committed under `artifacts/`.
- [ ] Evidence card can be validated before registry update.
"""


def _render_deviation_log(protocol_id: str) -> str:
    return f"""# Deviation Log: {protocol_id}

Record every deviation from the frozen protocol. If there were no deviations,
write `No deviations recorded`.

## Deviations

| Time | Step | What changed | Why | Effect on status |
| --- | --- | --- | --- | --- |

## Source Drift

| Source | Original reference | Fresh reference | Drift observed | Hash or note |
| --- | --- | --- | --- | --- |

## Manual Judgment

| Step | Judgment made | Was rule fixed before scoring? | Reviewer note |
| --- | --- | --- | --- |
"""


def _render_local_manifest(protocol_id: str) -> str:
    return f"""# Local Manifest: {protocol_id}

Use this file to list local-only files and hashes. Do not commit the files
listed here unless the public data policy explicitly allows it.

| Local path | SHA-256 or blocked reason | Public replacement |
| --- | --- | --- |
"""
