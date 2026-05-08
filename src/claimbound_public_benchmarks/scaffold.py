# SPDX-License-Identifier: Apache-2.0
"""Deterministic scaffold generation for ClaimBound tracks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class ScaffoldRequest:
    source_url: str
    protocol_id: str
    domain: str
    track_type: str
    execution_mode: str
    out_dir: Path
    source_name: str
    audience: str


def build_scaffold(request: ScaffoldRequest, repo_root: Path) -> list[Path]:
    """Create a draft protocol/playbook/checklist/card scaffold.

    The scaffold deliberately does not create a result status. A draft track is
    not evidence until an operator executes it and validates a completed card.
    """

    created_at = datetime.now(UTC).date().isoformat()
    protocol_id = _normalize_protocol_id(request.protocol_id)
    slug = protocol_id.lower()

    protocol_path = repo_root / "docs" / "protocols" / f"{protocol_id}_PREREG_CHARTER.md"
    request_path = repo_root / "docs" / "evidence_requests" / f"{protocol_id}_REQUEST.md"
    playbook_path = request.out_dir / f"{protocol_id}_PLAYBOOK.md"
    checklist_path = request.out_dir / f"{protocol_id}_CHECKLIST.md"
    declaration_path = request.out_dir / f"{protocol_id}_OPERATOR_DECLARATION.md"
    draft_card_path = repo_root / "docs" / "evidence_card_drafts" / f"CLAIMBOUND-{protocol_id}-DRAFT.json"
    source_probe_path = repo_root / "artifacts" / f"{slug}_source_probe_summary.json"

    request.out_dir.mkdir(parents=True, exist_ok=True)
    request_path.parent.mkdir(parents=True, exist_ok=True)
    protocol_path.parent.mkdir(parents=True, exist_ok=True)
    draft_card_path.parent.mkdir(parents=True, exist_ok=True)
    source_probe_path.parent.mkdir(parents=True, exist_ok=True)

    _write_text(request_path, _render_request(request, protocol_id))
    _write_text(protocol_path, _render_protocol(request, protocol_id, created_at))
    _write_text(playbook_path, _render_playbook(request, protocol_id))
    _write_text(checklist_path, _render_checklist(request, protocol_id))
    _write_text(declaration_path, _render_operator_declaration(protocol_id))
    _write_json(draft_card_path, _render_draft_card(request, protocol_id, created_at))
    _write_json(source_probe_path, _render_source_probe(request, protocol_id, created_at))

    return [
        protocol_path,
        request_path,
        playbook_path,
        checklist_path,
        declaration_path,
        draft_card_path,
        source_probe_path,
    ]


def _render_request(request: ScaffoldRequest, protocol_id: str) -> str:
    return f"""# Evidence Request: {protocol_id}

Status: request scaffold. This is not evidence.

## Public Claim

To be written narrowly by the requester before protocol freeze.

## Claim Source URL

{request.source_url}

## Narrow ClaimBound Question

Can this claim be checked under a frozen protocol with source boundary, scoring
rule, hashes, result status, limitation and rerun path?

## Main Audience

{request.audience}

## Preferred Track

{request.execution_mode}

## Proposed Sources

- {request.source_name}: {request.source_url}

## Proposed Scoring Or Resolution Rule

Not recorded yet. Must be fixed before execution.

## Known Reproducibility Risks

- source rights may be unclear;
- source access may change;
- prompt, payload, benchmark or transcript hashes may be unavailable;
- another operator may be unable to rerun the same environment.

## Claims This Card Must Not Make

- no broad model superiority claim;
- no deployment-readiness claim;
- no legal certification claim;
- no correctness claim outside this protocol.
"""


def _normalize_protocol_id(protocol_id: str) -> str:
    out = protocol_id.strip().upper().replace("-", "_").replace(" ", "_")
    if not out:
        raise ValueError("protocol_id must not be empty")
    return out


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_protocol(request: ScaffoldRequest, protocol_id: str, created_at: str) -> str:
    return f"""# {protocol_id} Pre-Registration Charter

Status: draft scaffold. This file is not a completed evidence record.

Created: {created_at}

## Claim Boundary

This track may check only a narrow `{request.track_type}` claim for the source
listed below. It must not claim broad model superiority, deployment readiness,
legal certification, or correctness outside this protocol.

## Source

- Source name: {request.source_name}
- Source URL: {request.source_url}
- Domain: {request.domain}
- Audience: {request.audience}
- Execution mode: {request.execution_mode}

## Fields To Freeze Before Execution

- exact public claim;
- official or public source boundary;
- source rights note;
- raw payload or transcript policy;
- target or question set;
- prompt set and prompt hash, when applicable;
- model or method identifier, when applicable;
- baselines and controls, when applicable;
- scoring or resolution rule;
- pass, negative, blocked and insufficient-coverage decision rules;
- stop conditions;
- forbidden after-result changes.

## Stop Conditions

Stop and record an honest blocked or insufficient status when source access,
rights, coverage, prompt disclosure, model identity, scoring, logs or hashes are
not good enough for a fair run.
"""


def _render_playbook(request: ScaffoldRequest, protocol_id: str) -> str:
    return f"""# {protocol_id} Playbook

This playbook is a scaffold. Follow it only after the protocol is reviewed and
frozen.

## Setup

```bash
uv sync --extra dev
uv run --extra dev python scripts/claimbound_validate_evidence_card.py --help
```

## Operator Flow

1. Open the public claim source: {request.source_url}
2. Record the exact claim being checked.
3. Freeze the protocol before collecting outcomes.
4. Create a run root outside this repository.
5. Record source rights and raw payload policy.
6. Collect local-only raw payloads, prompts, transcripts or logs.
7. Hash local-only artifacts.
8. Produce a sanitized summary in `artifacts/`.
9. Complete an evidence card JSON.
10. Run the evidence-card validator.
11. Update the registry only after validation.

## Expected Public Outputs

```text
docs/protocols/{protocol_id}_PREREG_CHARTER.md
docs/manual_audit/{protocol_id}_CHECKLIST.md
docs/evidence_cards/CLAIMBOUND-{protocol_id}-<DATE>.json
artifacts/{protocol_id.lower()}_summary.json
```
"""


def _render_checklist(request: ScaffoldRequest, protocol_id: str) -> str:
    return f"""# {protocol_id} Checklist

- [ ] Public claim source opens: {request.source_url}
- [ ] Exact claim is written narrowly.
- [ ] Official or public source boundary is recorded.
- [ ] Source rights and attribution note are recorded.
- [ ] Raw payload or transcript policy is recorded.
- [ ] Protocol file is frozen before execution.
- [ ] Prompt set or source selection is frozen before execution.
- [ ] Model/method identifier is recorded when applicable.
- [ ] Scoring or resolution rule is frozen before execution.
- [ ] Stop conditions are listed.
- [ ] Local-only raw artifacts are kept outside the repository.
- [ ] Raw artifact hashes or blocked reason are recorded.
- [ ] Sanitized public summary is created.
- [ ] Evidence card uses an exact documented result status.
- [ ] Evidence card states a narrow claim boundary.
- [ ] Evidence card validates.
- [ ] Registry update is made only after validation.
"""


def _render_operator_declaration(protocol_id: str) -> str:
    return f"""# {protocol_id} Operator Declaration

```text
I fixed source, selection, prompt or target, scoring rule, controls, stop
conditions and acceptance gate before outcome scoring.

I did not remove weak data after seeing outcomes.
I did not tune thresholds after seeing outcomes.
I did not rewrite a negative, blocked or limited result as a positive claim.
I recorded deviations and limitations.
```
"""


def _render_draft_card(
    request: ScaffoldRequest, protocol_id: str, created_at: str
) -> dict[str, object]:
    return {
        "evidence_id": f"CLAIMBOUND-{protocol_id}-DRAFT",
        "draft_status": "GRAY_DRAFT_NOT_EXECUTED",
        "registry_sequence": 0,
        "record_type": "protocol_registration",
        "protocol_id": protocol_id,
        "protocol_version": "DRAFT",
        "domain": request.domain,
        "claim_type": request.track_type,
        "execution_mode": request.execution_mode,
        "claim_boundary": (
            "Draft only. No result is claimed until a real run produces "
            "validated artifacts under the frozen protocol."
        ),
        "official_source_name": request.source_name,
        "official_source_url": request.source_url,
        "access_date": created_at,
        "source_rights_note": "NOT_RECORDED_YET",
        "raw_payload_committed": False,
        "raw_payload_manifest": "NOT_RECORDED_YET",
        "sanitized_report_path": "NOT_CREATED_YET",
        "sanitized_report_sha256": "NOT_CREATED_YET",
        "git_commit": "NOT_RECORDED_YET",
        "runner_command": "NOT_EXECUTED_YET",
        "operator": "NOT_RECORDED_YET",
        "created_at": created_at,
        "last_verified_date": "NOT_VERIFIED_YET",
        "verification_count": 0,
        "verification_level": "NOT_EXECUTED",
        "reproduction_level": "not executed",
        "ai_assistance": "not used for outcome selection or gate changes",
        "manual_review": "required before execution",
        "known_limitations": [
            "This is a scaffold, not evidence.",
            "No result status has been assigned.",
            "No broad claim is supported.",
        ],
    }


def _render_source_probe(
    request: ScaffoldRequest, protocol_id: str, created_at: str
) -> dict[str, object]:
    parsed = urlparse(request.source_url)
    return {
        "protocol_id": protocol_id,
        "created_at": created_at,
        "source_name": request.source_name,
        "source_url": request.source_url,
        "url_scheme": parsed.scheme,
        "url_netloc": parsed.netloc,
        "probe_mode": "static_scaffold_only",
        "network_fetch_performed": False,
        "rights_probe_status": "NOT_RECORDED_YET",
        "coverage_probe_status": "NOT_RECORDED_YET",
        "raw_payload_policy": "raw payloads must stay outside this repository",
        "claim_boundary": (
            "Static source probe scaffold only. This summary does not prove "
            "source access, source rights, coverage or result status."
        ),
        "unresolved_questions": [
            "Does the source allow the proposed use?",
            "Can required prompts, payloads, transcripts or benchmark items be hashed?",
            "Can another operator rerun the track?",
        ],
    }
