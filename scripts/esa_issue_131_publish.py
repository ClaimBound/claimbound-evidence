# SPDX-License-Identifier: Apache-2.0
"""Publication phase for the ESA issue #131 local batch runner."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

from esa_issue_131_common import (
    CARDS_DIR,
    MATRIX_EXPORT_PATH,
    REGISTRY_PATH,
    REPO_ROOT,
    RUNBOOK_RESULT_PATH,
    SUMMARY_PATH,
    read_json,
    registry_statistics,
    sha256_bytes,
    write_json,
)
from esa_issue_131_data import load_matrix
from esa_issue_131_preview import load_preview


def build_card(
    *,
    result: dict[str, Any],
    matrix_version: str,
    access_date: str,
    operator: str,
    sequence: int,
    summary_sha256: str,
) -> dict[str, Any]:
    protocol_id = str(result["protocol_id"])
    evidence_id = f"CLAIMBOUND-{protocol_id}-{access_date}"
    source_sha = result.get("source_sha256")
    status = str(result["result_status"])

    if status == "PASSED_UNDER_PROTOCOL":
        claim_boundary = (
            "This card verifies only that the official ESA mission page "
            "contained the frozen source terms supporting this narrow "
            f"statement: {result['claim']} It does not validate mission "
            "performance, product accuracy, completeness, safety or "
            "operational suitability."
        )
    elif status == "INSUFFICIENT_COVERAGE":
        claim_boundary = (
            "This card records that the official ESA mission page did "
            "not contain all frozen source terms required for this "
            f"narrow statement: {result['claim']} This is an "
            "insufficient-coverage result, not a claim that the "
            "statement is false."
        )
    else:
        claim_boundary = (
            "This card records that the official ESA source could not "
            "be retrieved under the frozen local protocol for this "
            f"narrow statement: {result['claim']} This is a "
            "blocked-source result, not a scientific conclusion."
        )

    card: dict[str, Any] = {
        "access_date": access_date,
        "ai_assistance": (
            "AI assisted preparation of the frozen issue #131 claim "
            "matrix; deterministic local regex gates selected the "
            "status; no gate was changed after preview."
        ),
        "baseline_control_summary": (
            "Frozen all-pattern source-boundary gate against one "
            "official ESA mission page; no non-ESA source entered the "
            "gate; missing patterns produce INSUFFICIENT_COVERAGE "
            "rather than a forced pass."
        ),
        "card_svg_rendered": (
            f"docs/evidence_cards/{evidence_id}.svg"
        ),
        "card_svg_template": (
            "docs/assets/claimbound_evidence_card.svg"
        ),
        "claim_boundary": claim_boundary,
        "claim_type": "source_boundary",
        "created_at": access_date,
        "domain": "public-data",
        "evidence_id": evidence_id,
        "evidence_url": (
            "https://github.com/ClaimBound/claimbound-evidence/"
            f"blob/main/docs/evidence_cards/{evidence_id}.json"
        ),
        "execution_mode": "AUTOMATED_AI_ASSISTED",
        "git_commit": "local-before-merge",
        "known_limitations": [
            "Single official ESA mission page only.",
            "One frozen source-boundary statement only.",
            "String-pattern presence is not scientific validation.",
            "No mission-performance, product-accuracy or operational "
            "certification claim is made.",
            "No independent reproduction has yet been recorded.",
        ],
        "last_verified_date": access_date,
        "manual_review": (
            "operator confirmed review of the frozen 100-card preview "
            "before publication"
        ),
        "official_source_name": result["official_source_name"],
        "official_source_url": result["official_source_url"],
        "operator": operator,
        "protocol_id": protocol_id,
        "protocol_version": matrix_version,
        "raw_payload_committed": False,
        "raw_payload_manifest": (
            f"official source SHA-256: {source_sha}; raw HTML retained "
            "only in local run root"
            if source_sha
            else "official source retrieval failed; no raw payload "
            "committed"
        ),
        "record_type": "source_audit",
        "registry_sequence": sequence,
        "reproduction_level": "not independently reproduced",
        "result_status": status,
        "runner_command": (
            "uv run python "
            "scripts/claimbound_run_esa_issue_131.py publish "
            "--preview <local-preview.json> --operator <handle> "
            "--confirm-reviewed"
        ),
        "sanitized_report_path": (
            "artifacts/esa_issue_131_batch_summary.json"
        ),
        "sanitized_report_sha256": summary_sha256,
        "source_rights_note": (
            "Official ESA public web page. Raw HTML is kept only in "
            "the local run root and is not committed."
        ),
        "verification_count": 1,
        "verification_level": "SINGLE_OPERATOR",
    }
    if status == "BLOCKED_SOURCE":
        card["block_reason"] = str(
            result.get("block_reason")
            or "official source unavailable"
        )
    return card


def registry_entry(
    card: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    return {
        "evidence_id": card["evidence_id"],
        "registry_sequence": card["registry_sequence"],
        "path": str(path.relative_to(REPO_ROOT)),
        "result_status": card["result_status"],
        "protocol_id": card["protocol_id"],
        "domain": card["domain"],
        "record_type": card["record_type"],
        "operator": card["operator"],
        "created_at": card["created_at"],
        "last_verified_date": card["last_verified_date"],
        "verification_level": card["verification_level"],
        "verification_count": card["verification_count"],
        "reproduction_level": card["reproduction_level"],
        "official_source_name": card["official_source_name"],
        "sanitized_report_path": card["sanitized_report_path"],
    }


def run_publish(
    *,
    preview_arg: str,
    operator: str,
    confirm_reviewed: bool,
) -> int:
    if not confirm_reviewed:
        raise SystemExit(
            "Refusing to publish: pass --confirm-reviewed only after "
            "reviewing preview.json"
        )

    preview_path = Path(preview_arg).expanduser().resolve()
    preview = load_preview(preview_path)
    matrix, matrix_payload = load_matrix()

    if preview.get("matrix_sha256") != sha256_bytes(matrix_payload):
        raise SystemExit(
            "Matrix changed after preview. Run preview again; "
            "post-result gate changes are forbidden."
        )

    matrix_by_id = {
        card["protocol_id"]: card
        for card in matrix["cards"]
    }
    results_by_id = {
        result["protocol_id"]: result
        for result in preview["results"]
    }
    if set(matrix_by_id) != set(results_by_id):
        raise SystemExit(
            "Preview protocol IDs do not match the frozen matrix"
        )

    registry = read_json(REGISTRY_PATH)
    registry_cards = registry.get("cards")
    if not isinstance(registry_cards, list):
        raise SystemExit("registry.cards must be a list")

    existing_by_protocol: dict[str, dict[str, Any]] = {}
    for entry in registry_cards:
        protocol_id = entry.get("protocol_id")
        if isinstance(protocol_id, str):
            existing_by_protocol[protocol_id] = entry

    existing_sequences = [
        int(entry["registry_sequence"])
        for entry in registry_cards
    ]
    next_sequence = max(existing_sequences, default=0) + 1

    planned_sequences: dict[str, int] = {}
    next_value = next_sequence
    for protocol_id in sorted(results_by_id):
        if protocol_id in existing_by_protocol:
            planned_sequences[protocol_id] = int(
                existing_by_protocol[protocol_id][
                    "registry_sequence"
                ]
            )
        else:
            planned_sequences[protocol_id] = next_value
            next_value += 1

    batch_rows: list[dict[str, Any]] = []
    for protocol_id in sorted(results_by_id):
        result = results_by_id[protocol_id]
        existing = existing_by_protocol.get(protocol_id)
        if existing is not None:
            existing_path = REPO_ROOT / str(existing["path"])
            if not existing_path.is_file():
                raise SystemExit(
                    f"{protocol_id}: existing registry path is missing"
                )
            existing_card = read_json(existing_path)
            if (
                existing_card.get("official_source_url")
                != result["official_source_url"]
            ):
                raise SystemExit(
                    f"{protocol_id}: existing source URL differs "
                    "from preview"
                )
            if (
                existing_card.get("result_status")
                != result["result_status"]
            ):
                raise SystemExit(
                    f"{protocol_id}: existing status "
                    f"{existing_card.get('result_status')} differs "
                    f"from preview {result['result_status']}"
                )

        batch_rows.append(
            {
                "protocol_id": protocol_id,
                "mission": result["mission"],
                "topic": result["topic"],
                "section": result["section"],
                "claim": result["claim"],
                "official_source_url": (
                    result["official_source_url"]
                ),
                "source_sha256": result.get("source_sha256"),
                "required_patterns": result["required_patterns"],
                "matched_patterns": result["matched_patterns"],
                "missing_patterns": result["missing_patterns"],
                "result_status": result["result_status"],
                "block_reason": result.get("block_reason"),
                "registry_sequence": (
                    planned_sequences[protocol_id]
                ),
                "publication_state": (
                    "existing"
                    if existing is not None
                    else "created"
                ),
            }
        )

    counts = dict(
        sorted(
            Counter(
                row["result_status"]
                for row in batch_rows
            ).items()
        )
    )
    summary = {
        "issue_number": 131,
        "matrix_version": matrix["version"],
        "matrix_sha256": preview["matrix_sha256"],
        "access_date": preview["access_date"],
        "operator": operator,
        "raw_payload_committed": False,
        "claim_boundary": (
            "This batch report records 100 frozen source-boundary "
            "evaluations against five official ESA Copernicus Sentinel "
            "mission pages. It does not certify mission performance, "
            "data quality, safety or operational suitability."
        ),
        "result_counts": counts,
        "source_records": [
            {
                key: value
                for key, value in record.items()
                if key != "raw_path"
            }
            for record in preview["source_records"]
        ],
        "cards": batch_rows,
    }
    summary_payload = (
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    summary_sha256 = sha256_bytes(summary_payload)

    temp_root = (
        preview_path.parent.parent
        / "generated_repository_files"
    )
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_cards = (
        temp_root / "docs" / "evidence_cards"
    )
    temp_cards.mkdir(parents=True, exist_ok=True)

    new_cards: list[
        tuple[dict[str, Any], Path, Path]
    ] = []
    for protocol_id in sorted(results_by_id):
        if protocol_id in existing_by_protocol:
            continue

        result = results_by_id[protocol_id]
        card = build_card(
            result=result,
            matrix_version=str(matrix["version"]),
            access_date=str(preview["access_date"]),
            operator=operator,
            sequence=planned_sequences[protocol_id],
            summary_sha256=summary_sha256,
        )
        violations = validate_evidence_card(card)
        if violations:
            joined = "; ".join(violations)
            raise SystemExit(
                f"{protocol_id}: generated card is invalid: "
                f"{joined}"
            )

        card_path = (
            CARDS_DIR / f"{card['evidence_id']}.json"
        )
        svg_path = (
            CARDS_DIR / f"{card['evidence_id']}.svg"
        )
        if card_path.exists() or svg_path.exists():
            raise SystemExit(
                f"{protocol_id}: target evidence file exists but "
                "protocol is absent from registry"
            )

        temp_card_path = temp_cards / card_path.name
        temp_svg_path = temp_cards / svg_path.name
        write_json(temp_card_path, card)
        temp_svg_path.write_text(
            render_svg(temp_card_path),
            encoding="utf-8",
        )
        new_cards.append(
            (card, card_path, svg_path)
        )

    updated_registry_cards = list(registry_cards)
    for card, card_path, _svg_path in new_cards:
        updated_registry_cards.append(
            registry_entry(card, card_path)
        )

    updated_registry_cards = sorted(
        updated_registry_cards,
        key=lambda entry: str(entry["evidence_id"]),
    )
    registry["cards"] = updated_registry_cards
    registry["card_count"] = len(
        updated_registry_cards
    )
    registry["statistics"] = registry_statistics(
        updated_registry_cards
    )

    temp_registry_path = (
        temp_root
        / "docs"
        / "registry"
        / "evidence_index.json"
    )
    temp_summary_path = (
        temp_root
        / "artifacts"
        / SUMMARY_PATH.name
    )
    temp_matrix_path = (
        temp_root
        / "docs"
        / "esa"
        / "issue_131_claim_matrix.json"
    )
    write_json(temp_registry_path, registry)
    temp_summary_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_summary_path.write_bytes(
        summary_payload
    )
    temp_matrix_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_matrix_path.write_bytes(
        matrix_payload
    )

    result_lines = [
        "# ESA issue #131: 100-card source-boundary batch",
        "",
        f"- Access date: `{preview['access_date']}`",
        f"- Operator: `{operator}`",
        f"- Matrix version: `{matrix['version']}`",
        f"- Matrix SHA-256: `{preview['matrix_sha256']}`",
        f"- Batch summary SHA-256: `{summary_sha256}`",
        "- Raw HTML committed: `false`",
        "",
        "## Result counts",
        "",
    ]
    for status, count in counts.items():
        result_lines.append(
            f"- `{status}`: {count}"
        )
    result_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Each card records one frozen string-presence "
            "source-boundary gate against one official ESA mission "
            "page. A passed card does not validate scientific "
            "accuracy, mission performance, completeness, safety or "
            "operational suitability.",
            "",
            "## Local validation",
            "",
            "```bash",
            "uv run claimbound validate-all",
            "uv run --extra dev python -m pytest -q",
            "```",
            "",
        ]
    )
    temp_result_readme = (
        temp_root
        / "docs"
        / "manual_audit"
        / "ESA-ISSUE-131"
        / "README.md"
    )
    temp_result_readme.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_result_readme.write_text(
        "\n".join(result_lines),
        encoding="utf-8",
    )

    for card, card_path, svg_path in new_cards:
        temp_card_path = (
            temp_cards / card_path.name
        )
        temp_svg_path = (
            temp_cards / svg_path.name
        )
        card_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        temp_card_path.replace(card_path)
        temp_svg_path.replace(svg_path)

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_summary_path.replace(SUMMARY_PATH)
    REGISTRY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_registry_path.replace(REGISTRY_PATH)
    RUNBOOK_RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_result_readme.replace(
        RUNBOOK_RESULT_PATH
    )
    MATRIX_EXPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temp_matrix_path.replace(
        MATRIX_EXPORT_PATH
    )

    print(f"created_cards={len(new_cards)}")
    print(
        "existing_target_cards="
        f"{100 - len(new_cards)}"
    )
    print("target_cards_total=100")
    print(
        f"registry_card_count="
        f"{registry['card_count']}"
    )
    for status, count in counts.items():
        print(f"{status}={count}")
    print(
        "batch_summary="
        f"{SUMMARY_PATH.relative_to(REPO_ROOT)}"
    )
    print(
        "Next: run validate-all and pytest "
        "before committing."
    )
    return 0
