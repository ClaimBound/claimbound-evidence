#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Preview and publish NASA factory issues #147 through #156."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

from nasa_factory_data import BATCH_ISSUES, load_matrix


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
CARDS_DIR = REPO_ROOT / "docs" / "evidence_cards"
USER_AGENT = (
    "Mozilla/5.0 ClaimBound/1.0 "
    "(public NASA source-boundary audit; ClaimBound/claimbound-evidence)"
)


def _paths(issue_number: int) -> dict[str, Path]:
    return {
        "matrix": REPO_ROOT
        / "docs"
        / "nasa"
        / f"issue_{issue_number}_claim_matrix.json",
        "summary": REPO_ROOT
        / "artifacts"
        / f"nasa_issue_{issue_number}_batch_summary.json",
        "result": (
            REPO_ROOT
            / "docs"
            / "manual_audit"
            / f"NASA-ISSUE-{issue_number}"
            / "README.md"
        ),
    }


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _write_json(path: Path, data: object) -> bytes:
    payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def _normalize_html(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    for before, after in {
        "\xa0": " ",
        "’": "'",
        "‘": "'",
        "–": "-",
        "—": "-",
        "‑": "-",
        "−": "-",
    }.items():
        text = text.replace(before, after)
    return re.sub(r"\s+", " ", text).strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _statistics(cards: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    def count(field: str) -> dict[str, int]:
        values = Counter(str(entry.get(field, "")) for entry in cards)
        values.pop("", None)
        return dict(sorted(values.items()))

    return {
        "by_domain": count("domain"),
        "by_record_type": count("record_type"),
        "by_result_status": count("result_status"),
        "by_source": count("official_source_name"),
    }


def _fetch_source(url: str) -> tuple[bytes | None, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read(), {
                "fetch_error": None,
                "canonical_url": response.geturl(),
                "http_status": response.status,
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, {
            "fetch_error": f"{type(exc).__name__}: {exc}",
            "canonical_url": None,
            "http_status": None,
        }


def _evaluate_card(card: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    if source["fetch_error"] is not None:
        matched: list[str] = []
        missing = list(card["required_patterns"])
        status = "BLOCKED_SOURCE"
        block_reason = source["fetch_error"]
        source_sha256 = None
    else:
        normalized = str(source["normalized_text"])
        matched = []
        missing = []
        for pattern in card["required_patterns"]:
            target = str(pattern)
            if re.search(target, normalized, flags=re.I):
                matched.append(target)
            else:
                missing.append(target)
        if card["gate_type"] == "manual_overclaim_boundary":
            status = "INSUFFICIENT_COVERAGE"
            missing = ["manual review required; no automatic absence-based pass"]
        else:
            status = "PASSED_UNDER_PROTOCOL" if not missing else "INSUFFICIENT_COVERAGE"
        block_reason = None
        source_sha256 = source["sha256"]

    return {
        "protocol_id": card["protocol_id"],
        "mission": card["mission"],
        "topic": card["topic"],
        "gate_type": card["gate_type"],
        "claim": card["claim"],
        "official_source_name": card["official_source_name"],
        "official_source_url": card["source_url"],
        "required_patterns": card["required_patterns"],
        "matched_patterns": matched,
        "missing_patterns": missing,
        "result_status": status,
        "block_reason": block_reason,
        "source_sha256": source_sha256,
    }


def _run_preview(issue_number: int, run_root_arg: str | None, quiet: bool) -> int:
    matrix, matrix_payload = load_matrix(issue_number)
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_root = (
        Path(run_root_arg).expanduser().resolve()
        if run_root_arg
        else Path.home() / "claimbound_runs" / f"NASA_ISSUE_{issue_number}_{timestamp}"
    )
    raw_dir = run_root / "raw"
    reports_dir = run_root / "reports"
    raw_dir.mkdir(parents=True, exist_ok=False)
    reports_dir.mkdir(parents=True, exist_ok=False)

    cards_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in matrix["cards"]:
        cards_by_url[str(card["source_url"])].append(card)

    source_records: dict[str, dict[str, Any]] = {}
    for source_url, source_cards in cards_by_url.items():
        mission = str(source_cards[0]["mission"])
        payload, fetch_metadata = _fetch_source(source_url)
        if payload is None:
            source_records[source_url] = {
                "mission": mission,
                "official_source_name": source_cards[0]["official_source_name"],
                "source_url": source_url,
                **fetch_metadata,
                "sha256": None,
                "raw_path": None,
                "normalized_text": "",
            }
            continue

        raw_path = raw_dir / f"{_slug(mission)}.html"
        raw_path.write_bytes(payload)
        source_records[source_url] = {
            "mission": mission,
            "official_source_name": source_cards[0]["official_source_name"],
            "source_url": source_url,
            **fetch_metadata,
            "sha256": _sha256(payload),
            "raw_path": str(raw_path),
            "normalized_text": _normalize_html(payload),
        }

    results = [
        _evaluate_card(card, source_records[str(card["source_url"])])
        for card in matrix["cards"]
    ]
    counts = dict(sorted(Counter(row["result_status"] for row in results).items()))
    preview = {
        "issue_number": issue_number,
        "matrix_source": "frozen issue-derived matrix; exported during publish",
        "matrix_sha256": _sha256(matrix_payload),
        "matrix_version": matrix["version"],
        "created_at": now.isoformat(),
        "access_date": now.date().isoformat(),
        "run_root": str(run_root),
        "raw_payload_committed": False,
        "claim_boundary": (
            "This local preview evaluates exactly 50 frozen narrow claims "
            "against five official NASA mission pages. It records canonical URL, "
            "HTTP result and SHA-256; raw HTML remains outside "
            "the repository."
        ),
        "source_records": [
            {key: value for key, value in record.items() if key != "normalized_text"}
            for record in source_records.values()
        ],
        "result_counts": counts,
        "results": results,
    }
    preview_path = reports_dir / "preview.json"
    _write_json(preview_path, preview)

    if quiet:
        print(preview_path)
    else:
        print(f"preview_path={preview_path}")
        print(f"access_date={preview['access_date']}")
        print(f"card_count={len(results)}")
        for status, count in counts.items():
            print(f"{status}={count}")
        print("Review the preview before publishing. No repository files were changed.")
    return 0


def _load_preview(path: Path, issue_number: int) -> dict[str, Any]:
    preview = _read_json(path)
    if preview.get("issue_number") != issue_number:
        raise ValueError(f"preview is not for issue #{issue_number}")
    results = preview.get("results")
    if not isinstance(results, list) or len(results) != 50:
        raise ValueError("preview must contain exactly 50 results")
    return preview


def _build_card(
    *,
    issue_number: int,
    result: dict[str, Any],
    matrix_version: str,
    access_date: str,
    operator: str,
    sequence: int,
    summary_sha256: str,
) -> dict[str, Any]:
    protocol_id = str(result["protocol_id"])
    evidence_id = f"CLAIMBOUND-{protocol_id}-{access_date}"
    status = str(result["result_status"])
    source_sha = result.get("source_sha256")
    if status == "PASSED_UNDER_PROTOCOL":
        claim_boundary = (
            "This card verifies only that the official NASA mission page contained "
            "the frozen source terms supporting this narrow statement: "
            f"{result['claim']} It does not validate scientific accuracy, mission "
            "performance, completeness, safety or operational suitability."
        )
    elif status == "INSUFFICIENT_COVERAGE":
        claim_boundary = (
            "This card records that the official NASA mission page did not contain "
            "all frozen source terms required for this narrow statement: "
            f"{result['claim']} This is an insufficient-coverage result, not a "
            "claim that the statement is false."
        )
    else:
        claim_boundary = (
            "This card records that the official NASA source could not be retrieved "
            "under the frozen local protocol for this narrow statement: "
            f"{result['claim']} This is a blocked-source result, not a scientific "
            "conclusion."
        )

    summary_path = f"artifacts/nasa_issue_{issue_number}_batch_summary.json"
    card: dict[str, Any] = {
        "access_date": access_date,
        "ai_assistance": (
            f"AI-assisted drafting of the frozen issue #{issue_number} claim matrix; "
            "deterministic local regex gates selected the status; the operator "
            "reviews the preview before publication."
        ),
        "baseline_control_summary": (
            "Frozen all-pattern source-boundary gate against one official NASA "
            "mission page; no non-NASA source entered the gate; missing patterns "
            "produce INSUFFICIENT_COVERAGE rather than a forced pass."
        ),
        "card_svg_rendered": f"docs/evidence_cards/{evidence_id}.svg",
        "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
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
            "Single official NASA mission page only.",
            "One frozen source-boundary statement only.",
            "String-pattern presence is not scientific validation.",
            "No mission-performance, product-accuracy or operational certification claim is made.",
            "No independent reproduction has yet been recorded.",
        ],
        "last_verified_date": access_date,
        "manual_review": (
            f"operator confirmed review of the frozen issue #{issue_number} "
            "50-card preview before publication"
        ),
        "official_source_name": result["official_source_name"],
        "official_source_url": result["official_source_url"],
        "operator": operator,
        "protocol_id": protocol_id,
        "protocol_version": matrix_version,
        "raw_payload_committed": False,
        "raw_payload_manifest": (
            f"official source SHA-256: {source_sha}; raw HTML retained only in local run root"
            if source_sha
            else "official source retrieval failed; no raw payload committed"
        ),
        "record_type": "source_audit",
        "registry_sequence": sequence,
        "reproduction_level": "not independently reproduced",
        "result_status": status,
        "runner_command": (
            "uv run python scripts/claimbound_run_nasa_factory.py "
            f"--issue {issue_number} publish --preview <local-preview.json> "
            "--operator <handle> --confirm-reviewed"
        ),
        "sanitized_report_path": summary_path,
        "sanitized_report_sha256": summary_sha256,
        "source_rights_note": (
            "Official NASA public web page. Raw HTML is kept only in the local "
            "run root and is not committed."
        ),
        "verification_count": 1,
        "verification_level": "SINGLE_OPERATOR",
    }
    if status == "BLOCKED_SOURCE":
        card["block_reason"] = str(
            result.get("block_reason") or "official source unavailable"
        )
    return card


def _registry_entry(card: dict[str, Any], path: Path) -> dict[str, Any]:
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


def _run_publish(
    issue_number: int,
    preview_arg: str,
    operator: str,
    confirm_reviewed: bool,
) -> int:
    if not confirm_reviewed:
        raise SystemExit(
            "Refusing to publish: pass --confirm-reviewed only after reviewing preview.json"
        )
    preview_path = Path(preview_arg).expanduser().resolve()
    preview = _load_preview(preview_path, issue_number)
    matrix, matrix_payload = load_matrix(issue_number)
    if preview.get("matrix_sha256") != _sha256(matrix_payload):
        raise SystemExit(
            "Matrix changed after preview. Run preview again; post-result gate changes are forbidden."
        )

    matrix_ids = {card["protocol_id"] for card in matrix["cards"]}
    results_by_id = {row["protocol_id"]: row for row in preview["results"]}
    if matrix_ids != set(results_by_id):
        raise SystemExit("Preview protocol IDs do not match the frozen matrix")

    registry = _read_json(REGISTRY_PATH)
    registry_cards = registry.get("cards")
    if not isinstance(registry_cards, list):
        raise SystemExit("registry.cards must be a list")
    existing_by_protocol = {
        str(entry["protocol_id"]): entry
        for entry in registry_cards
        if isinstance(entry, dict) and isinstance(entry.get("protocol_id"), str)
    }
    next_sequence = (
        max((int(entry["registry_sequence"]) for entry in registry_cards), default=0)
        + 1
    )
    planned_sequences: dict[str, int] = {}
    for protocol_id in sorted(results_by_id):
        existing = existing_by_protocol.get(protocol_id)
        if existing is not None:
            planned_sequences[protocol_id] = int(existing["registry_sequence"])
        else:
            planned_sequences[protocol_id] = next_sequence
            next_sequence += 1

    batch_rows: list[dict[str, Any]] = []
    for protocol_id in sorted(results_by_id):
        result = results_by_id[protocol_id]
        existing = existing_by_protocol.get(protocol_id)
        if existing is not None:
            existing_path = REPO_ROOT / str(existing["path"])
            if not existing_path.is_file():
                raise SystemExit(f"{protocol_id}: existing registry path is missing")
            existing_card = _read_json(existing_path)
            if (
                existing_card.get("official_source_url")
                != result["official_source_url"]
            ):
                raise SystemExit(
                    f"{protocol_id}: existing source URL differs from preview"
                )
            if existing_card.get("result_status") != result["result_status"]:
                raise SystemExit(f"{protocol_id}: existing status differs from preview")
        batch_rows.append(
            {
                "protocol_id": protocol_id,
                "mission": result["mission"],
                "topic": result["topic"],
                "gate_type": result["gate_type"],
                "claim": result["claim"],
                "official_source_url": result["official_source_url"],
                "source_sha256": result.get("source_sha256"),
                "required_patterns": result["required_patterns"],
                "matched_patterns": result["matched_patterns"],
                "missing_patterns": result["missing_patterns"],
                "result_status": result["result_status"],
                "block_reason": result.get("block_reason"),
                "registry_sequence": planned_sequences[protocol_id],
                "publication_state": "existing" if existing is not None else "created",
            }
        )

    counts = dict(sorted(Counter(row["result_status"] for row in batch_rows).items()))
    paths = _paths(issue_number)
    summary = {
        "issue_number": issue_number,
        "matrix_version": matrix["version"],
        "matrix_sha256": preview["matrix_sha256"],
        "access_date": preview["access_date"],
        "operator": operator,
        "raw_payload_committed": False,
        "claim_boundary": (
            "This batch report records 50 frozen source-boundary evaluations "
            "against five official NASA mission pages. It does not certify mission "
            "performance, data quality, safety or operational suitability."
        ),
        "result_counts": counts,
        "source_records": [
            {key: value for key, value in record.items() if key != "raw_path"}
            for record in preview["source_records"]
        ],
        "cards": batch_rows,
    }
    summary_payload = (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    summary_sha256 = _sha256(summary_payload)

    temp_root = preview_path.parent.parent / "generated_repository_files"
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_cards = temp_root / "docs" / "evidence_cards"
    temp_cards.mkdir(parents=True, exist_ok=True)

    new_cards: list[tuple[dict[str, Any], Path, Path]] = []
    cards_to_write: list[tuple[dict[str, Any], Path, Path]] = []
    for protocol_id in sorted(results_by_id):
        result = results_by_id[protocol_id]
        existing = existing_by_protocol.get(protocol_id)
        card = _build_card(
            issue_number=issue_number,
            result=result,
            matrix_version=str(matrix["version"]),
            access_date=str(preview["access_date"]),
            operator=operator,
            sequence=planned_sequences[protocol_id],
            summary_sha256=summary_sha256,
        )
        violations = validate_evidence_card(card)
        if violations:
            raise SystemExit(
                f"{protocol_id}: generated card is invalid: {'; '.join(violations)}"
            )
        card_path = CARDS_DIR / f"{card['evidence_id']}.json"
        svg_path = CARDS_DIR / f"{card['evidence_id']}.svg"
        if existing is None and (card_path.exists() or svg_path.exists()):
            raise SystemExit(
                f"{protocol_id}: evidence file exists but protocol is absent from registry"
            )
        temp_card_path = temp_cards / card_path.name
        temp_svg_path = temp_cards / svg_path.name
        _write_json(temp_card_path, card)
        temp_svg_path.write_text(render_svg(temp_card_path), encoding="utf-8")
        cards_to_write.append((card, card_path, svg_path))
        if existing is None:
            new_cards.append((card, card_path, svg_path))

    updated_registry_cards = list(registry_cards)
    for card, card_path, _svg_path in new_cards:
        updated_registry_cards.append(_registry_entry(card, card_path))
    updated_registry_cards.sort(key=lambda entry: str(entry["evidence_id"]))
    registry["cards"] = updated_registry_cards
    registry["card_count"] = len(updated_registry_cards)
    registry["statistics"] = _statistics(updated_registry_cards)

    temp_registry = temp_root / "docs" / "registry" / "evidence_index.json"
    temp_summary = temp_root / "artifacts" / paths["summary"].name
    temp_matrix = temp_root / "docs" / "nasa" / paths["matrix"].name
    _write_json(temp_registry, registry)
    temp_summary.parent.mkdir(parents=True, exist_ok=True)
    temp_summary.write_bytes(summary_payload)
    temp_matrix.parent.mkdir(parents=True, exist_ok=True)
    temp_matrix.write_bytes(matrix_payload)

    result_lines = [
        f"# NASA issue #{issue_number}: 50-card source-boundary batch",
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
    result_lines.extend(f"- `{status}`: {count}" for status, count in counts.items())
    result_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.",
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
    temp_result = (
        temp_root / "docs" / "manual_audit" / f"NASA-ISSUE-{issue_number}" / "README.md"
    )
    temp_result.parent.mkdir(parents=True, exist_ok=True)
    temp_result.write_text("\n".join(result_lines), encoding="utf-8")

    for _card, card_path, svg_path in cards_to_write:
        (temp_cards / card_path.name).replace(card_path)
        (temp_cards / svg_path.name).replace(svg_path)
    paths["summary"].parent.mkdir(parents=True, exist_ok=True)
    temp_summary.replace(paths["summary"])
    temp_registry.replace(REGISTRY_PATH)
    paths["matrix"].parent.mkdir(parents=True, exist_ok=True)
    temp_matrix.replace(paths["matrix"])
    paths["result"].parent.mkdir(parents=True, exist_ok=True)
    temp_result.replace(paths["result"])

    print(f"created_cards={len(new_cards)}")
    print(f"refreshed_existing_cards={len(cards_to_write) - len(new_cards)}")
    print(f"existing_target_cards={50 - len(new_cards)}")
    print("target_cards_total=50")
    print(f"registry_card_count={registry['card_count']}")
    for status, count in counts.items():
        print(f"{status}={count}")
    print(f"batch_summary={paths['summary'].relative_to(REPO_ROOT)}")
    print("Next: run validate-all and pytest before committing.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", type=int, choices=list(BATCH_ISSUES), required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Validate the frozen 50-card matrix.")

    preview = commands.add_parser(
        "preview", help="Fetch five NASA pages and write a local-only preview."
    )
    preview.add_argument("--run-root")
    preview.add_argument("--quiet", action="store_true")

    publish = commands.add_parser(
        "publish", help="Publish cards from a reviewed frozen preview."
    )
    publish.add_argument("--preview", required=True)
    publish.add_argument("--operator", required=True)
    publish.add_argument("--confirm-reviewed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "check":
            matrix, payload = load_matrix(args.issue)
            print(f"matrix_cards={len(matrix['cards'])}")
            print(f"matrix_sha256={_sha256(payload)}")
            print("matrix_status=VALID")
            return 0
        if args.command == "preview":
            return _run_preview(args.issue, args.run_root, args.quiet)
        return _run_publish(
            args.issue,
            args.preview,
            args.operator,
            args.confirm_reviewed,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
