#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the interactive and static ESA 500-card evidence atlas."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES = range(131, 136)
ATLAS_DIR = REPO_ROOT / "docs" / "esa" / "atlas"
DATA_JSON_PATH = ATLAS_DIR / "atlas-data.json"
DATA_JS_PATH = ATLAS_DIR / "atlas-data.js"
HEATMAP_PATH = REPO_ROOT / "docs" / "assets" / "esa_500_heatmap.svg"
REGISTRY_PATH = REPO_ROOT / "docs" / "registry" / "evidence_index.json"

SLOT_LABELS = [
    "Purpose / primary gate",
    "Programme / design gate",
    "Design / instrument gate",
    "Instrument / measurement gate",
    "Target / launch gate",
    "Science / launch gate",
    "Launch timing gate",
    "Launch site gate",
    "Launch vehicle gate",
    "Orbit / destination gate",
    "Numeric fact 1",
    "Numeric fact 2",
    "Data / operations gate",
    "Products / archive gate",
    "Documents / factsheet gate",
    "Images / media gate",
    "Latest story gate",
    "Overclaim boundary gate",
    "Rerun / drift gate",
    "Registration / access gate",
]

PROTOCOL_RE = re.compile(
    r"^ESA-(?P<prefix>.+)-(?P<slot>[0-9]{2})-D(?P<dataset>[0-9]+)$"
)


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


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
    mission_issue: dict[str, int] = {}
    access_dates: set[str] = set()

    for batch_index, issue_number in enumerate(ISSUES, start=1):
        summary_path = (
            REPO_ROOT / "artifacts" / f"esa_issue_{issue_number}_batch_summary.json"
        )
        summary = _read_json(summary_path)
        summary_cards = summary.get("cards")
        sources = summary.get("source_records")
        if not isinstance(summary_cards, list) or len(summary_cards) != 100:
            raise ValueError(f"issue #{issue_number}: expected 100 cards")
        if not isinstance(sources, list) or len(sources) != 5:
            raise ValueError(f"issue #{issue_number}: expected five source records")

        access_date = str(summary["access_date"])
        access_dates.add(access_date)
        source_by_url = {str(row["source_url"]): row for row in sources}
        batch_missions = [str(row["mission"]) for row in sources]
        mission_order.extend(batch_missions)
        for mission in batch_missions:
            if mission in mission_issue:
                raise ValueError(f"mission appears in multiple batches: {mission}")
            mission_issue[mission] = issue_number

        for row in summary_cards:
            protocol_id = str(row["protocol_id"])
            match = PROTOCOL_RE.fullmatch(protocol_id)
            if match is None:
                raise ValueError(f"unexpected ESA factory protocol ID: {protocol_id}")
            slot = int(match.group("slot"))
            if not 1 <= slot <= 20:
                raise ValueError(f"{protocol_id}: slot must be between 01 and 20")
            mission = str(row["mission"])
            if mission not in batch_missions:
                raise ValueError(f"{protocol_id}: mission missing from source records")
            source_url = str(row["official_source_url"])
            source = source_by_url.get(source_url)
            if source is None:
                raise ValueError(
                    f"{protocol_id}: source URL missing from source records"
                )

            registry_row = registry_by_protocol.get(protocol_id)
            if registry_row is None:
                raise ValueError(f"{protocol_id}: missing from registry")
            evidence_path = REPO_ROOT / str(registry_row["path"])
            if not evidence_path.is_file():
                raise ValueError(f"{protocol_id}: registry path does not exist")
            evidence = _read_json(evidence_path)
            if evidence.get("result_status") != row["result_status"]:
                raise ValueError(f"{protocol_id}: status differs from evidence card")
            if evidence.get("official_source_url") != source_url:
                raise ValueError(f"{protocol_id}: source differs from evidence card")

            cards.append(
                {
                    "protocol_id": protocol_id,
                    "evidence_id": evidence["evidence_id"],
                    "evidence_path": str(registry_row["path"]),
                    "svg_path": str(evidence["card_svg_rendered"]),
                    "issue_number": issue_number,
                    "batch_index": batch_index,
                    "mission": mission,
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
                    "standardized_slot_semantics": issue_number >= 132,
                }
            )

        batches.append(
            {
                "issue_number": issue_number,
                "batch_index": batch_index,
                "label": f"Batch {(batch_index - 1) * 100 + 1:03d}-{batch_index * 100:03d}",
                "missions": batch_missions,
                "access_date": access_date,
                "result_counts": dict(
                    sorted(
                        Counter(
                            str(row["result_status"]) for row in summary_cards
                        ).items()
                    )
                ),
            }
        )

    if len(cards) != 500:
        raise ValueError(f"atlas must contain 500 cards, found {len(cards)}")
    protocol_ids = [str(row["protocol_id"]) for row in cards]
    if len(set(protocol_ids)) != 500:
        raise ValueError("atlas contains duplicate protocol IDs")
    if len(mission_order) != 25 or len(set(mission_order)) != 25:
        raise ValueError("atlas must contain 25 unique missions")

    cards_by_mission: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        cards_by_mission[str(card["mission"])].append(card)
    for mission, mission_cards in cards_by_mission.items():
        slots = {int(card["slot"]) for card in mission_cards}
        if slots != set(range(1, 21)):
            raise ValueError(f"{mission}: expected one card in every slot")

    mission_rank = {mission: index for index, mission in enumerate(mission_order)}
    cards.sort(key=lambda row: (mission_rank[str(row["mission"])], int(row["slot"])))
    result_counts = dict(
        sorted(Counter(str(row["result_status"]) for row in cards).items())
    )
    slot_statistics = []
    for slot, slot_label in enumerate(SLOT_LABELS, start=1):
        slot_cards = [row for row in cards if row["slot"] == slot]
        slot_statistics.append(
            {
                "slot": slot,
                "label": slot_label,
                "result_counts": dict(
                    sorted(
                        Counter(str(row["result_status"]) for row in slot_cards).items()
                    )
                ),
            }
        )

    return {
        "schema_version": "1.0",
        "title": "ESA 500-card evidence atlas",
        "generated_from_issues": list(ISSUES),
        "access_date_range": {
            "from": min(access_dates),
            "to": max(access_dates),
        },
        "card_count": len(cards),
        "mission_count": len(mission_order),
        "slot_count": len(SLOT_LABELS),
        "result_counts": result_counts,
        "mission_order": mission_order,
        "slot_labels": [
            {"slot": index, "label": label}
            for index, label in enumerate(SLOT_LABELS, start=1)
        ],
        "slot_statistics": slot_statistics,
        "batches": batches,
        "cards": cards,
        "interpretation": {
            "rows": "Each row is one official ESA mission landing page.",
            "columns": (
                "Columns are protocol slot positions 01-20. Issues #132-#135 "
                "use standardized slot semantics; issue #131 uses mission-specific gates."
            ),
            "status": (
                "A pass records exact source-term presence under the frozen gate. "
                "Limited coverage records missing source terms, not a false mission fact."
            ),
        },
    }


def _render_heatmap(atlas: dict[str, Any]) -> str:
    cards_by_mission = {
        mission: [row for row in atlas["cards"] if row["mission"] == mission]
        for mission in atlas["mission_order"]
    }
    x_grid = 324
    y_grid = 174
    cell_width = 38
    cell_height = 20
    row_step = 23
    batch_gap = 11

    rows: list[str] = []
    y = y_grid
    mission_number = 0
    for batch in atlas["batches"]:
        batch_start = y
        for mission in batch["missions"]:
            mission_number += 1
            cards = cards_by_mission[str(mission)]
            cells = []
            for card in cards:
                slot = int(card["slot"])
                status = str(card["result_status"])
                css_class = "limited" if status == "INSUFFICIENT_COVERAGE" else "passed"
                symbol = "!" if css_class == "limited" else str(slot).zfill(2)
                cells.append(
                    f'<rect x="{x_grid + (slot - 1) * cell_width}" y="{y}" '
                    f'width="33" height="{cell_height}" rx="4" class="{css_class}"/>'
                    f'<text x="{x_grid + (slot - 1) * cell_width + 16.5}" '
                    f'y="{y + 14}" class="cell-text">{symbol}</text>'
                )
            rows.append(
                f'<text x="104" y="{y + 15}" class="mission">{escape(str(mission))}</text>'
                + "".join(cells)
            )
            y += row_step
        batch_height = y - batch_start - 3
        rows.append(
            f'<rect x="36" y="{batch_start}" width="48" height="{batch_height}" '
            'rx="8" class="batch-band"/>'
            f'<text x="60" y="{batch_start + batch_height / 2}" '
            f'class="batch-label" transform="rotate(-90 60 {batch_start + batch_height / 2})">'
            f"#{batch['issue_number']}</text>"
        )
        y += batch_gap

    column_labels = "".join(
        f'<text x="{x_grid + (slot - 1) * cell_width + 16.5}" y="151" '
        f'class="column">{slot:02d}</text>'
        for slot in range(1, 21)
    )
    legend_items = []
    legend_y = y + 39
    for index, item in enumerate(atlas["slot_labels"]):
        column = index // 5
        row = index % 5
        legend_items.append(
            f'<text x="{40 + column * 288}" y="{legend_y + row * 23}" class="slot-key">'
            f"{int(item['slot']):02d}  {escape(str(item['label']))}</text>"
        )
    height = legend_y + 5 * 23 + 36

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
  <title id="title">ESA 500-card mission by protocol-slot heatmap</title>
  <desc id="desc">Twenty-five ESA mission rows and twenty protocol-slot columns show 490 passed source gates and ten limited-coverage gates.</desc>
  <defs>
    <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f5f0e4"/>
      <stop offset="1" stop-color="#e8e3d5"/>
    </linearGradient>
    <style>
      .title {{ fill: #17383a; font: 700 29px Georgia, serif; }}
      .sub {{ fill: #5c6d69; font: 600 13px 'Trebuchet MS', sans-serif; letter-spacing: 1.2px; }}
      .metric {{ fill: #17383a; font: 700 27px Georgia, serif; }}
      .metric-label {{ fill: #6b7772; font: 600 11px 'Trebuchet MS', sans-serif; letter-spacing: .7px; }}
      .mission {{ fill: #243d3d; font: 600 12px 'Trebuchet MS', sans-serif; }}
      .column {{ fill: #596c68; font: 700 10px 'Trebuchet MS', sans-serif; text-anchor: middle; }}
      .passed {{ fill: #2d9273; }}
      .limited {{ fill: #d6842d; }}
      .cell-text {{ fill: #fffdf5; font: 700 9px 'Trebuchet MS', sans-serif; text-anchor: middle; }}
      .batch-band {{ fill: #17383a; }}
      .batch-label {{ fill: #f4d67f; font: 700 11px 'Trebuchet MS', sans-serif; text-anchor: middle; letter-spacing: 1px; }}
      .slot-key {{ fill: #405754; font: 600 11px 'Trebuchet MS', sans-serif; }}
      .rule {{ stroke: #c9c2b1; stroke-width: 1; }}
      .note {{ fill: #5d6b68; font: 500 12px 'Trebuchet MS', sans-serif; }}
    </style>
  </defs>
  <rect width="1200" height="{height}" rx="22" fill="url(#paper)"/>
  <text x="40" y="45" class="sub">CLAIMBOUND / OFFICIAL ESA SOURCE BOUNDARIES</text>
  <text x="40" y="86" class="title">Where the evidence is — and where it is not</text>
  <text x="750" y="74" class="metric">25 × 20</text>
  <text x="750" y="96" class="metric-label">MISSIONS × PROTOCOL SLOTS</text>
  <text x="912" y="74" class="metric">490</text>
  <text x="912" y="96" class="metric-label">PASSED</text>
  <text x="1030" y="74" class="metric">10</text>
  <text x="1030" y="96" class="metric-label">LIMITED</text>
  <line x1="40" y1="119" x2="1160" y2="119" class="rule"/>
  <text x="104" y="151" class="column" text-anchor="start">MISSION</text>
  {column_labels}
  {"".join(rows)}
  <line x1="40" y1="{y + 13}" x2="1160" y2="{y + 13}" class="rule"/>
  <rect x="870" y="{y + 27}" width="18" height="18" rx="4" class="passed"/>
  <text x="896" y="{y + 41}" class="note">exact source terms present</text>
  <rect x="1040" y="{y + 27}" width="18" height="18" rx="4" class="limited"/>
  <text x="1066" y="{y + 41}" class="note">terms absent</text>
  {"".join(legend_items)}
</svg>
"""


def main() -> int:
    atlas = collect_atlas()
    _write_json(DATA_JSON_PATH, atlas)
    DATA_JS_PATH.write_text(
        "window.ESA_ATLAS_DATA = "
        + json.dumps(atlas, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    HEATMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEATMAP_PATH.write_text(_render_heatmap(atlas), encoding="utf-8")
    print(f"cards={atlas['card_count']}")
    print(f"missions={atlas['mission_count']}")
    print(f"slots={atlas['slot_count']}")
    print(f"result_counts={atlas['result_counts']}")
    print(f"data={DATA_JSON_PATH.relative_to(REPO_ROOT)}")
    print(f"heatmap={HEATMAP_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
