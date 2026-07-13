#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the ESA 500-card campaign summary and README visual."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES = range(131, 136)
SUMMARY_PATH = REPO_ROOT / "docs" / "esa" / "esa_500_summary.json"
SVG_PATH = REPO_ROOT / "docs" / "assets" / "esa_500_landscape.svg"
REGISTRY_PATH = REPO_ROOT / "docs" / "registry" / "evidence_index.json"


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


def _collect() -> dict[str, Any]:
    registry = _read_json(REGISTRY_PATH)
    registry_cards = registry.get("cards")
    if not isinstance(registry_cards, list):
        raise ValueError("registry.cards must be a list")
    registry_protocols = {str(row.get("protocol_id", "")) for row in registry_cards}

    campaign_cards: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    access_dates: set[str] = set()
    for issue_number in ISSUES:
        path = REPO_ROOT / "artifacts" / f"esa_issue_{issue_number}_batch_summary.json"
        batch = _read_json(path)
        cards = batch.get("cards")
        sources = batch.get("source_records")
        if not isinstance(cards, list) or len(cards) != 100:
            raise ValueError(f"issue #{issue_number}: expected exactly 100 cards")
        if not isinstance(sources, list) or len(sources) != 5:
            raise ValueError(f"issue #{issue_number}: expected exactly five sources")
        campaign_cards.extend(cards)
        access_dates.add(str(batch["access_date"]))
        batches.append(
            {
                "issue_number": issue_number,
                "card_count": len(cards),
                "missions": [str(source["mission"]) for source in sources],
                "result_counts": dict(
                    sorted(Counter(str(row["result_status"]) for row in cards).items())
                ),
            }
        )

    protocol_ids = [str(row["protocol_id"]) for row in campaign_cards]
    if len(protocol_ids) != 500 or len(set(protocol_ids)) != 500:
        raise ValueError("ESA campaign must contain 500 unique protocol IDs")
    missing_from_registry = sorted(set(protocol_ids) - registry_protocols)
    if missing_from_registry:
        raise ValueError(
            f"campaign cards missing from registry: {missing_from_registry}"
        )

    result_counts = dict(
        sorted(Counter(str(row["result_status"]) for row in campaign_cards).items())
    )
    mission_names = [mission for batch in batches for mission in batch["missions"]]
    insufficient = [
        {
            "protocol_id": row["protocol_id"],
            "mission": row["mission"],
            "topic": row["topic"],
            "missing_patterns": row["missing_patterns"],
            "official_source_url": row["official_source_url"],
        }
        for row in campaign_cards
        if row["result_status"] == "INSUFFICIENT_COVERAGE"
    ]
    esa_registry_cards = [
        row
        for row in registry_cards
        if str(row.get("protocol_id", "")).startswith("ESA-")
    ]
    return {
        "campaign": "ESA 500-card source-boundary campaign",
        "access_dates": sorted(access_dates),
        "access_date_range": {
            "from": min(access_dates),
            "to": max(access_dates),
        },
        "factory_issue": 130,
        "batch_issues": list(ISSUES),
        "card_count": len(campaign_cards),
        "mission_count": len(set(mission_names)),
        "official_source_count": len(set(mission_names)),
        "result_counts": result_counts,
        "pass_rate_percent": round(
            100 * result_counts.get("PASSED_UNDER_PROTOCOL", 0) / len(campaign_cards),
            1,
        ),
        "registry_context": {
            "all_registry_cards": int(registry["card_count"]),
            "all_esa_cards": len(esa_registry_cards),
            "preexisting_esa_showcase_cards": len(esa_registry_cards)
            - len(campaign_cards),
        },
        "batches": batches,
        "insufficient_coverage": insufficient,
        "interpretation": (
            "The ten insufficient-coverage results mean that the selected ESA "
            "mission landing pages did not expose the frozen launch-site or "
            "launch-vehicle marker. They do not claim that the mission facts are false."
        ),
    }


def _render_svg(summary: dict[str, Any]) -> str:
    batches = summary["batches"]
    access_range = summary["access_date_range"]
    access_label = str(access_range["from"])
    if access_range["from"] != access_range["to"]:
        access_label += f" TO {access_range['to']}"
    blocks: list[str] = []
    for index, batch in enumerate(batches):
        x = 52 + index * 220
        issue_number = int(batch["issue_number"])
        missions = batch["missions"]
        counts = batch["result_counts"]
        passed = int(counts.get("PASSED_UNDER_PROTOCOL", 0))
        limited = int(counts.get("INSUFFICIENT_COVERAGE", 0))
        mission_lines = "".join(
            f'<text x="{x + 18}" y="{286 + row * 23}" class="mission">{escape(str(mission))}</text>'
            for row, mission in enumerate(missions)
        )
        blocks.append(
            f"""
  <g>
    <rect x="{x}" y="188" width="196" height="232" rx="18" class="batch"/>
    <text x="{x + 18}" y="220" class="eyebrow">ISSUE #{issue_number}</text>
    <text x="{x + 18}" y="256" class="batch-total">100 gates</text>
    {mission_lines}
    <rect x="{x + 18}" y="389" width="160" height="8" rx="4" class="track"/>
    <rect x="{x + 18}" y="389" width="{1.6 * passed:.1f}" height="8" rx="4" class="pass"/>
    <text x="{x + 18}" y="414" class="status">{passed} pass / {limited} limited</text>
  </g>"""
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560" role="img" aria-labelledby="title desc">
  <title id="title">ESA 500-card source-boundary atlas</title>
  <desc id="desc">Five batches cover 25 ESA missions with 500 evidence cards: 490 passed and 10 recorded insufficient source coverage.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071b2b"/>
      <stop offset="0.58" stop-color="#0c3140"/>
      <stop offset="1" stop-color="#144f55"/>
    </linearGradient>
    <radialGradient id="glow" cx="82%" cy="8%" r="72%">
      <stop offset="0" stop-color="#f2cc67" stop-opacity=".26"/>
      <stop offset="1" stop-color="#f2cc67" stop-opacity="0"/>
    </radialGradient>
    <style>
      .title {{ fill: #f8faf5; font: 700 34px Georgia, serif; letter-spacing: .5px; }}
      .sub {{ fill: #a9c9c8; font: 500 15px 'Trebuchet MS', sans-serif; letter-spacing: 1.4px; }}
      .metric {{ fill: #f8faf5; font: 700 46px Georgia, serif; }}
      .metric-label {{ fill: #b9d2cf; font: 600 13px 'Trebuchet MS', sans-serif; letter-spacing: .7px; }}
      .batch {{ fill: #0d2836; stroke: #41616a; stroke-width: 1; }}
      .eyebrow {{ fill: #f2cc67; font: 700 12px 'Trebuchet MS', sans-serif; letter-spacing: 1.2px; }}
      .batch-total {{ fill: #f8faf5; font: 700 24px Georgia, serif; }}
      .mission {{ fill: #c8dcda; font: 500 13px 'Trebuchet MS', sans-serif; }}
      .status {{ fill: #8fb3b2; font: 600 11px 'Trebuchet MS', sans-serif; }}
      .track {{ fill: #a96d2c; }}
      .pass {{ fill: #38a67a; }}
      .finding {{ fill: #e3eeee; font: 600 14px 'Trebuchet MS', sans-serif; }}
      .finding-label {{ fill: #f2cc67; font: 700 12px 'Trebuchet MS', sans-serif; letter-spacing: 1.1px; }}
    </style>
  </defs>
  <rect width="1200" height="560" rx="24" fill="url(#bg)"/>
  <rect width="1200" height="560" rx="24" fill="url(#glow)"/>
  <path d="M0 148 H1200" stroke="#41616a" stroke-opacity=".55"/>
  <text x="52" y="55" class="sub">CLAIMBOUND / OFFICIAL ESA SOURCES / {access_label}</text>
  <text x="52" y="99" class="title">ESA source-boundary atlas</text>
  <text x="665" y="91" class="metric">500</text>
  <text x="665" y="119" class="metric-label">CARDS</text>
  <text x="810" y="91" class="metric">25</text>
  <text x="810" y="119" class="metric-label">MISSIONS</text>
  <text x="940" y="91" class="metric">98%</text>
  <text x="940" y="119" class="metric-label">SOURCE GATES PASSED</text>
  {"".join(blocks).lstrip()}
  <rect x="52" y="452" width="1096" height="62" rx="15" fill="#09212e" stroke="#41616a"/>
  <text x="72" y="478" class="finding-label">THE HONEST FINDING</text>
  <text x="72" y="500" class="finding">10 gaps, all in launch-site or launch-vehicle fields omitted from five selected mission landing pages.</text>
  <circle cx="1086" cy="483" r="8" fill="#38a67a"/>
  <text x="1102" y="488" class="status">490 pass</text>
  <circle cx="1086" cy="504" r="8" fill="#d59039"/>
  <text x="1102" y="509" class="status">10 limited</text>
</svg>
"""


def main() -> int:
    summary = _collect()
    _write_json(SUMMARY_PATH, summary)
    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(_render_svg(summary), encoding="utf-8")
    print(f"summary={SUMMARY_PATH.relative_to(REPO_ROOT)}")
    print(f"visual={SVG_PATH.relative_to(REPO_ROOT)}")
    print(f"cards={summary['card_count']}")
    print(f"missions={summary['mission_count']}")
    print(f"result_counts={summary['result_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
