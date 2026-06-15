#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build validated EU source-audit evidence cards from frozen runner summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = REPO_ROOT / "docs" / "evidence_cards"
RUNNER = REPO_ROOT / "scripts" / "claimbound_run_eu_public_source_audit.py"
RENDERER = REPO_ROOT / "scripts" / "claimbound_render_evidence_card_svg.py"


@dataclass(frozen=True)
class CardSpec:
    profile: str
    evidence_suffix: str
    sequence: int
    artifact: Path
    allowed_claim_sentence: str
    baseline_control_summary: str
    candidate_definition: str
    controls_and_gate: str


SPECS = (
    CardSpec(
        profile="EU_ODP_SOURCE_AUDIT_D001",
        evidence_suffix="EU_ODP_SOURCE_AUDIT_D001",
        sequence=19,
        artifact=REPO_ROOT / "artifacts" / "eu_odp_source_audit_d001_summary.json",
        allowed_claim_sentence="EU Data Portal landing page passed source audit",
        baseline_control_summary=(
            "Source audit controls required HTTP 200, HTML content, European Data Portal "
            "title marker, dataset catalog link, hub search API link and copyright notice link."
        ),
        candidate_definition="European Data Portal landing page",
        controls_and_gate="HTTP 200 + title marker + catalog/API/copyright links",
    ),
    CardSpec(
        profile="EEA_LEGAL_REUSE_SOURCE_AUDIT_D001",
        evidence_suffix="EEA_LEGAL_REUSE_SOURCE_AUDIT_D001",
        sequence=20,
        artifact=REPO_ROOT / "artifacts" / "eea_legal_reuse_source_audit_d001_summary.json",
        allowed_claim_sentence="EEA content reuse FAQ passed source audit",
        baseline_control_summary=(
            "Source audit controls required HTTP 200, HTML content, EEA reuse FAQ title "
            "marker, legal-notice link and FAQs index link."
        ),
        candidate_definition="EEA content reuse FAQ page",
        controls_and_gate="HTTP 200 + title marker + legal notice + FAQ navigation links",
    ),
    CardSpec(
        profile="EUROSTAT_SOURCE_AUDIT_D001",
        evidence_suffix="EUROSTAT_SOURCE_AUDIT_D001",
        sequence=21,
        artifact=REPO_ROOT / "artifacts" / "eurostat_source_audit_d001_summary.json",
        allowed_claim_sentence="Eurostat API guidelines page passed source audit",
        baseline_control_summary=(
            "Source audit controls required HTTP 200, HTML content, API guidelines title "
            "marker, copyright notice link and catalogue API documentation links."
        ),
        candidate_definition="Eurostat API detailed guidelines page",
        controls_and_gate="HTTP 200 + title marker + copyright + catalogue API doc links",
    ),
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-reports",
        action="store_true",
        help="Fetch live source pages before rebuilding cards. Default: use existing summaries.",
    )
    parser.add_argument(
        "--access-date",
        default=None,
        help=(
            "ISO access date for refreshed reports, or fallback date for legacy summaries "
            "that do not yet contain access_date."
        ),
    )
    return parser


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_short_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()


def _run_profile(spec: CardSpec, access_date: str | None) -> None:
    command = [sys.executable, str(RUNNER), "--profile", spec.profile]
    if access_date:
        command.extend(["--access-date", access_date])
    subprocess.check_call(command, cwd=REPO_ROOT)


def _report_access_date(report: dict[str, object], fallback: str | None) -> str:
    access_date = str(report.get("access_date") or fallback or "")
    if not access_date:
        raise ValueError(
            "summary report is missing access_date; pass --access-date for legacy summaries "
            "or refresh reports with --refresh-reports"
        )
    return access_date


def _build_card(
    spec: CardSpec,
    report: dict[str, object],
    git_commit: str,
    access_date: str,
) -> dict[str, object]:
    rel_artifact = spec.artifact.relative_to(REPO_ROOT).as_posix()
    evidence_id = f"CLAIMBOUND-{spec.evidence_suffix}-{access_date}"
    card_path = f"docs/evidence_cards/{evidence_id}.json"
    page_sha = str(report.get("page_sha256", ""))
    return {
        "access_date": access_date,
        "ai_assistance": (
            "AI assisted with runner implementation and card drafting; "
            "deterministic HTTP/source-boundary checks produced the report."
        ),
        "allowed_claim_sentence": spec.allowed_claim_sentence,
        "baseline_control_summary": spec.baseline_control_summary,
        "card_svg_rendered": card_path.replace(".json", ".svg"),
        "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
        "card_validity_level": report.get("card_validity_level", "GREEN_VALIDATED"),
        "claim_boundary": report["claim_boundary"],
        "claim_type": "source_audit",
        "created_at": access_date,
        "domain": "public-data",
        "evidence_id": evidence_id,
        "execution_mode": "AUTOMATED_AI_ASSISTED",
        "git_commit": git_commit,
        "known_limitations": report["known_limitations"],
        "last_verified_date": access_date,
        "manual_review": (
            "Source boundary, no-raw-payload policy and claim boundary reviewed "
            "in this repository update."
        ),
        "official_source_name": report["official_source_name"],
        "official_source_url": report["official_source_url"],
        "operator": "local operator",
        "protocol_id": spec.profile,
        "protocol_version": f"SOURCE-AUDIT-{access_date}",
        "raw_payload_committed": False,
        "raw_payload_manifest": (
            f"external source page SHA-256 {page_sha}; no raw HTML committed"
        ),
        "record_type": "source_audit",
        "registry_sequence": spec.sequence,
        "reproduction_level": "not independently reproduced",
        "result_status": report["result_status"],
        "runner_command": (
            f"uv run python scripts/claimbound_run_eu_public_source_audit.py "
            f"--profile {spec.profile}"
        ),
        "sanitized_report_path": rel_artifact,
        "sanitized_report_sha256": _sha256(spec.artifact),
        "source_rights_note": (
            "Official EU public-source page used for source-boundary evidence only; "
            "this card records access date, local hash, link presence and limitations. "
            "No legal conclusion is made."
        ),
        "verification_count": 1,
        "verification_level": "SINGLE_OPERATOR",
        "visual_summary": {
            "allowed_claim_sentence": spec.allowed_claim_sentence,
            "artifact_ref": f"page sha256 + {rel_artifact}",
            "candidate_definition": spec.candidate_definition,
            "controls_and_gate": spec.controls_and_gate,
            "evidence_url": card_path,
            "period_scope": f"source page accessed {access_date}",
            "target_definition": "EU public-data source boundary",
        },
    }


def main() -> int:
    args = _build_parser().parse_args()
    git_commit = _git_short_commit()
    for spec in SPECS:
        if args.refresh_reports:
            _run_profile(spec, args.access_date)
        report = json.loads(spec.artifact.read_text(encoding="utf-8"))
        access_date = _report_access_date(report, args.access_date)
        card = _build_card(spec, report, git_commit, access_date)
        card_path = CARDS_DIR / f"{card['evidence_id']}.json"
        card_path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
        svg_path = card_path.with_suffix(".svg")
        subprocess.check_call(
            [sys.executable, str(RENDERER), card_path, svg_path],
            cwd=REPO_ROOT,
        )
        print(card_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
