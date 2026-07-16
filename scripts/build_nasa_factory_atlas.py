#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the interactive and static NASA 500-card evidence atlas."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES = range(147, 157)
ATLAS_DIR = REPO_ROOT / "docs" / "nasa" / "atlas"
DATA_JSON_PATH = ATLAS_DIR / "atlas-data.json"
DATA_JS_PATH = ATLAS_DIR / "atlas-data.js"
HEATMAP_PATH = REPO_ROOT / "docs" / "assets" / "nasa_500_heatmap.svg"
REGISTRY_PATH = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
SLOT_LABELS = [
    "Purpose / primary gate",
    "Programme / partner boundary",
    "Design / architecture gate",
    "Instrument / system gate",
    "Target / measurement gate",
    "Status / timeline gate",
    "Orbit / trajectory / destination gate",
    "Numeric or first-of-kind fact gate",
    "Public output / data path gate",
    "Overclaim / later-drift boundary",
]
PROTOCOL_RE = re.compile(r"^NASA-(?P<prefix>.+)-(?P<slot>[0-9]{2})-D(?P<dataset>[0-9]+)$")


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def collect_atlas() -> dict[str, Any]:
    registry = _read_json(REGISTRY_PATH)
    registry_rows = registry.get("cards")
    if not isinstance(registry_rows, list):
        raise ValueError("registry.cards must be a list")
    registry_by_protocol = {
        str(row["protocol_id"]): row
        for row in registry_rows
        if isinstance(row, dict) and isinstance(row.get("protocol_id"), str)
    }

    cards: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    mission_order: list[str] = []
    access_dates: set[str] = set()
    for batch_index, issue_number in enumerate(ISSUES, start=1):
        summary = _read_json(REPO_ROOT / "artifacts" / f"nasa_issue_{issue_number}_batch_summary.json")
        summary_cards = summary.get("cards")
        sources = summary.get("source_records")
        if not isinstance(summary_cards, list) or len(summary_cards) != 50:
            raise ValueError(f"issue #{issue_number}: expected 50 cards")
        if not isinstance(sources, list) or len(sources) != 5:
            raise ValueError(f"issue #{issue_number}: expected five source records")
        access_date = str(summary["access_date"])
        access_dates.add(access_date)
        source_by_url = {str(row["source_url"]): row for row in sources}
        batch_missions = [str(row["mission"]) for row in sources]
        mission_order.extend(batch_missions)

        for row in summary_cards:
            protocol_id = str(row["protocol_id"])
            match = PROTOCOL_RE.fullmatch(protocol_id)
            if match is None:
                raise ValueError(f"unexpected NASA protocol ID: {protocol_id}")
            slot = int(match.group("slot"))
            if not 1 <= slot <= 10:
                raise ValueError(f"{protocol_id}: slot must be 01 through 10")
            source_url = str(row["official_source_url"])
            source = source_by_url.get(source_url)
            registry_row = registry_by_protocol.get(protocol_id)
            if source is None or registry_row is None:
                raise ValueError(f"{protocol_id}: source or registry entry missing")
            evidence_path = REPO_ROOT / str(registry_row["path"])
            evidence = _read_json(evidence_path)
            if evidence.get("result_status") != row["result_status"]:
                raise ValueError(f"{protocol_id}: status differs from evidence card")
            cards.append(
                {
                    "protocol_id": protocol_id,
                    "evidence_id": evidence["evidence_id"],
                    "evidence_path": str(registry_row["path"]),
                    "svg_path": str(evidence["card_svg_rendered"]),
                    "issue_number": issue_number,
                    "batch_index": batch_index,
                    "mission": row["mission"],
                    "slot": slot,
                    "slot_label": SLOT_LABELS[slot - 1],
                    "topic": row["topic"],
                    "claim": row["claim"],
                    "result_status": row["result_status"],
                    "official_source_name": source["official_source_name"],
                    "official_source_url": source_url,
                    "source_sha256": row.get("source_sha256"),
                    "access_date": access_date,
                    "missing_patterns": row.get("missing_patterns", []),
                    "gate_type": row["gate_type"],
                }
            )
        batches.append(
            {
                "issue_number": issue_number,
                "batch_index": batch_index,
                "label": f"Batch {(batch_index - 1) * 50 + 1:03d}-{batch_index * 50:03d}",
                "missions": batch_missions,
                "access_date": access_date,
                "result_counts": dict(sorted(Counter(str(row["result_status"]) for row in summary_cards).items())),
            }
        )

    if len(cards) != 500 or len(set(str(card["protocol_id"]) for card in cards)) != 500:
        raise ValueError("NASA atlas must contain 500 unique protocol IDs")
    if len(mission_order) != 50 or len(set(mission_order)) != 50:
        raise ValueError("NASA atlas must contain 50 unique mission pages")
    by_mission: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        by_mission[str(card["mission"])].append(card)
    if any({int(card["slot"]) for card in rows} != set(range(1, 11)) for rows in by_mission.values()):
        raise ValueError("each NASA mission must have one card in every slot")
    rank = {mission: index for index, mission in enumerate(mission_order)}
    cards.sort(key=lambda row: (rank[str(row["mission"])], int(row["slot"])))
    result_counts = dict(sorted(Counter(str(row["result_status"]) for row in cards).items()))
    return {
        "schema_version": "1.0",
        "title": "NASA 500-card evidence atlas",
        "generated_from_issues": list(ISSUES),
        "access_date_range": {"from": min(access_dates), "to": max(access_dates)},
        "card_count": len(cards),
        "mission_count": len(mission_order),
        "slot_count": len(SLOT_LABELS),
        "result_counts": result_counts,
        "mission_order": mission_order,
        "slot_labels": [{"slot": index, "label": label} for index, label in enumerate(SLOT_LABELS, start=1)],
        "batches": batches,
        "cards": cards,
        "interpretation": {
            "rows": "Each row is one selected official NASA page.",
            "columns": "Columns are frozen protocol positions, not mission scores.",
            "status": "A pass records only the frozen lexical source-boundary gate; limited coverage and manual-boundary records remain visible.",
        },
    }


def _render_heatmap(atlas: dict[str, Any]) -> str:
    by_mission = {mission: [row for row in atlas["cards"] if row["mission"] == mission] for mission in atlas["mission_order"]}
    x_grid, y_grid, cell_width, row_step, batch_gap = 300, 175, 66, 21, 8
    rows: list[str] = []
    y = y_grid
    for batch in atlas["batches"]:
        start = y
        for mission in batch["missions"]:
            cells = "".join(
                f'<rect x="{x_grid + (int(card["slot"]) - 1) * cell_width}" y="{y}" width="55" height="17" rx="3" class="{"passed" if card["result_status"] == "PASSED_UNDER_PROTOCOL" else "limited"}"/>'
                for card in by_mission[str(mission)]
            )
            rows.append(f'<text x="105" y="{y + 13}" class="mission">{escape(str(mission))}</text>{cells}')
            y += row_step
        rows.append(f'<text x="45" y="{start + 32}" class="batch">#{batch["issue_number"]}</text>')
        y += batch_gap
    columns = "".join(f'<text x="{x_grid + (slot - 1) * cell_width + 27}" y="151" class="column">{slot:02d}</text>' for slot in range(1, 11))
    height = y + 140
    passed = atlas["result_counts"].get("PASSED_UNDER_PROTOCOL", 0)
    limited = atlas["result_counts"].get("INSUFFICIENT_COVERAGE", 0)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">
  <title id="title">NASA 500-card mission by protocol-slot heatmap</title>
  <desc id="desc">Fifty official NASA pages by ten frozen source-boundary slots.</desc>
  <style>.title{{fill:#17383a;font:700 29px Georgia,serif}}.sub{{fill:#5c6d69;font:600 12px sans-serif;letter-spacing:1px}}.metric{{fill:#17383a;font:700 25px Georgia,serif;text-anchor:middle}}.mission{{fill:#243d3d;font:600 10px sans-serif}}.column{{fill:#596c68;font:700 10px sans-serif;text-anchor:middle}}.batch{{fill:#a76b28;font:700 12px sans-serif}}.passed{{fill:#2d9273}}.limited{{fill:#d6842d}}.note{{fill:#5d6b68;font:500 11px sans-serif}}</style>
  <rect width="1000" height="{height}" rx="20" fill="#f5f0e4"/>
  <text x="40" y="42" class="sub">CLAIMBOUND / OFFICIAL NASA SOURCE BOUNDARIES</text>
  <text x="40" y="80" class="title">NASA evidence coverage — and its limits</text>
  <text x="690" y="72" class="metric">50 × 10</text><text x="820" y="72" class="metric">{passed}</text><text x="930" y="72" class="metric">{limited}</text>
  <text x="690" y="94" class="sub" text-anchor="middle">PAGES × SLOTS</text><text x="820" y="94" class="sub" text-anchor="middle">PASSED</text><text x="930" y="94" class="sub" text-anchor="middle">LIMITED</text>
  <line x1="40" y1="119" x2="960" y2="119" stroke="#c9c2b1"/><text x="105" y="151" class="column" text-anchor="start">MISSION</text>{columns}{''.join(rows)}
  <text x="40" y="{y + 34}" class="note">Green: frozen lexical terms appeared in the selected source. Amber: limited coverage, including all 50 manual overclaim/drift boundaries without an automatic pass.</text>
</svg>'''


def main() -> int:
    atlas = collect_atlas()
    _write_json(DATA_JSON_PATH, atlas)
    DATA_JS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_JS_PATH.write_text("window.NASA_ATLAS_DATA = " + json.dumps(atlas, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    HEATMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEATMAP_PATH.write_text(_render_heatmap(atlas), encoding="utf-8")
    print(f"cards={atlas['card_count']}")
    print(f"missions={atlas['mission_count']}")
    print(f"slots={atlas['slot_count']}")
    print(f"result_counts={atlas['result_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
