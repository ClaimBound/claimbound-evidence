# SPDX-License-Identifier: Apache-2.0
"""Preview phase for the ESA issue #131 local batch runner."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from esa_issue_131_common import (
    USER_AGENT,
    normalize_html,
    sha256_bytes,
    slug,
    utc_now,
    write_json,
)
from esa_issue_131_data import load_matrix


def fetch_source(url: str) -> tuple[bytes | None, str | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read(), None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def evaluate_card(
    card: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    if source["fetch_error"] is not None:
        return {
            "protocol_id": card["protocol_id"],
            "mission": card["mission"],
            "topic": card["topic"],
            "section": card["section"],
            "claim": card["claim"],
            "official_source_name": card["official_source_name"],
            "official_source_url": card["source_url"],
            "required_patterns": card["required_patterns"],
            "matched_patterns": [],
            "missing_patterns": list(card["required_patterns"]),
            "result_status": "BLOCKED_SOURCE",
            "block_reason": source["fetch_error"],
            "source_sha256": None,
        }

    normalized = str(source["normalized_text"])
    matched: list[str] = []
    missing: list[str] = []
    for pattern in card["required_patterns"]:
        if re.search(str(pattern), normalized, flags=re.I):
            matched.append(str(pattern))
        else:
            missing.append(str(pattern))

    status = (
        "PASSED_UNDER_PROTOCOL"
        if not missing
        else "INSUFFICIENT_COVERAGE"
    )
    return {
        "protocol_id": card["protocol_id"],
        "mission": card["mission"],
        "topic": card["topic"],
        "section": card["section"],
        "claim": card["claim"],
        "official_source_name": card["official_source_name"],
        "official_source_url": card["source_url"],
        "required_patterns": card["required_patterns"],
        "matched_patterns": matched,
        "missing_patterns": missing,
        "result_status": status,
        "block_reason": None,
        "source_sha256": source["sha256"],
    }


def run_preview(
    *,
    run_root_arg: str | None,
    quiet: bool,
) -> int:
    matrix, matrix_payload = load_matrix()

    now = utc_now()
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    access_date = now.date().isoformat()
    run_root = (
        Path(run_root_arg).expanduser().resolve()
        if run_root_arg
        else Path.home()
        / "claimbound_runs"
        / f"ESA_ISSUE_131_{timestamp}"
    )
    raw_dir = run_root / "raw"
    reports_dir = run_root / "reports"
    raw_dir.mkdir(parents=True, exist_ok=False)
    reports_dir.mkdir(parents=True, exist_ok=True)

    source_records: dict[str, dict[str, Any]] = {}
    cards_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in matrix["cards"]:
        cards_by_url[str(card["source_url"])].append(card)

    for source_url, source_cards in cards_by_url.items():
        mission = str(source_cards[0]["mission"])
        raw_path = raw_dir / f"{slug(mission)}.html"
        payload, error = fetch_source(source_url)
        if payload is None:
            source_records[source_url] = {
                "mission": mission,
                "official_source_name": (
                    source_cards[0]["official_source_name"]
                ),
                "source_url": source_url,
                "fetch_error": error,
                "sha256": None,
                "raw_path": None,
                "normalized_text": "",
            }
        else:
            raw_path.write_bytes(payload)
            source_records[source_url] = {
                "mission": mission,
                "official_source_name": (
                    source_cards[0]["official_source_name"]
                ),
                "source_url": source_url,
                "fetch_error": None,
                "sha256": sha256_bytes(payload),
                "raw_path": str(raw_path),
                "normalized_text": normalize_html(payload),
            }

    results = [
        evaluate_card(
            card,
            source_records[str(card["source_url"])],
        )
        for card in matrix["cards"]
    ]
    counts = dict(
        sorted(
            Counter(
                result["result_status"]
                for result in results
            ).items()
        )
    )

    preview = {
        "issue_number": 131,
        "matrix_source": (
            "embedded frozen matrix; exported during publish"
        ),
        "matrix_sha256": sha256_bytes(matrix_payload),
        "matrix_version": matrix["version"],
        "created_at": now.isoformat(),
        "access_date": access_date,
        "run_root": str(run_root),
        "raw_payload_committed": False,
        "claim_boundary": (
            "This local preview evaluates exactly 100 frozen narrow "
            "claims against five official ESA mission pages. Raw HTML "
            "remains outside the repository."
        ),
        "source_records": [
            {
                key: value
                for key, value in record.items()
                if key != "normalized_text"
            }
            for record in source_records.values()
        ],
        "result_counts": counts,
        "results": results,
    }

    preview_path = reports_dir / "preview.json"
    write_json(preview_path, preview)

    if quiet:
        print(preview_path)
    else:
        print(f"preview_path={preview_path}")
        print(f"access_date={access_date}")
        print(f"card_count={len(results)}")
        for status, count in counts.items():
            print(f"{status}={count}")
        print(
            "Review the preview before publishing. "
            "No repository files were changed."
        )
    return 0


def load_preview(path: Path) -> dict[str, Any]:
    import json

    preview = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(preview, dict):
        raise ValueError("preview must be a JSON object")
    if preview.get("issue_number") != 131:
        raise ValueError("preview is not for issue #131")
    results = preview.get("results")
    if not isinstance(results, list) or len(results) != 100:
        raise ValueError("preview must contain exactly 100 results")
    return preview
