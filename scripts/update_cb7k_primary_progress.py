#!/usr/bin/env python3
"""Refresh CB7K primary-source progress counter from the registry."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/registry/evidence_index.json"
PROGRESS = ROOT / "docs/public_claims/CB7K_PRIMARY_SOURCE_PROGRESS.md"

DOMAIN_TITLES = {
    54: "Water quality",
    55: "Oceans",
    56: "Forests",
    57: "Biodiversity",
    58: "Agriculture",
    59: "Fisheries",
    60: "Mining",
    61: "Chemicals",
    62: "Waste management",
    63: "Recycling",
    64: "Plastics",
    65: "Renewable energy",
    66: "Power grid",
    67: "Nuclear energy",
    68: "Oil and gas",
    69: "Batteries",
    70: "Hydrogen",
    71: "Aviation",
    72: "Rail",
    73: "Public transit",
    74: "Road safety",
    75: "Shipping",
    76: "Logistics",
    77: "Electric vehicles",
    78: "Buildings",
    79: "Housing",
    80: "Construction",
    81: "Urban planning",
    82: "Satellites",
    83: "Earth observation",
    84: "Weather services",
    85: "Disaster response",
    86: "Education",
    87: "Universities",
    88: "Open science",
    89: "Academic publishing",
    90: "Journalism",
    91: "Advertising",
    92: "E-commerce",
    93: "Consumer products",
    94: "Product recalls",
    95: "Labor markets",
    96: "Wages and pay",
    97: "Workplace safety",
    98: "Sports",
    99: "Tourism",
    100: "Cultural heritage",
}


def counts() -> tuple[int, int, int | None]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    primary = 0
    wikidata = 0
    primary_domains: set[int] = set()
    for card in registry["cards"]:
        evidence_id = card.get("evidence_id", "")
        if not evidence_id.startswith("CLAIMBOUND-CB7K-"):
            continue
        match = re.search(r"DOM(\d{3})", evidence_id)
        path = card.get("sanitized_report_path") or ""
        if "primary_claims" in path:
            primary += 1
            if match:
                primary_domains.add(int(match.group(1)))
        elif "wikidata" in path:
            wikidata += 1
    next_domain = None
    for domain in range(1, 101):
        if domain not in primary_domains:
            next_domain = domain
            break
    return primary, wikidata, next_domain


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", action="append", default=[], help="DOMNNN: Title — Source")
    args = parser.parse_args()
    primary, remaining, next_domain = counts()
    domains_left = remaining // 70
    next_title = DOMAIN_TITLES.get(next_domain or -1, "unknown")
    next_label = (
        f"**DOM{next_domain:03d}** {next_title}" if next_domain else "**none** (complete)"
    )
    text = PROGRESS.read_text(encoding="utf-8")
    counter = f"""## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **{primary:,} / 7,000** |
| Remaining | **{remaining:,}** ({domains_left} domains × 70) |
| Next domain | {next_label} |
| Last updated | {date.today().isoformat()} |
"""
    text = re.sub(r"## Counter\n\n(?:.*?\n)*?(?=## )", counter + "\n", text, count=1, flags=re.S)
    # Keep summary band numbers aligned with counter.
    done_end = (next_domain - 1) if next_domain else 100
    summary_done = f"| Done | DOM001–DOM{done_end:03d} | {primary:,} |"
    summary_remain = (
        f"| Remaining | DOM{next_domain:03d}–DOM100 | {remaining:,} |"
        if next_domain
        else "| Remaining | — | 0 |"
    )
    text = re.sub(r"\| Done \| DOM001–DOM\d{3} \| [\d,]+ \|", summary_done, text, count=1)
    text = re.sub(r"\| Remaining \| .*? \| [\d,]+ \|", summary_remain, text, count=1)
    if args.latest:
        block = "Latest packs:\n" + "\n".join(f"- {item}" for item in args.latest) + "\n"
        if "Latest packs:" in text:
            text = re.sub(r"Latest packs:\n(?:- .*\n)+", block, text, count=1)
        else:
            text = text.replace(
                "Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.\n",
                "Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.\n\n" + block,
            )
    # Queue next line
    text = re.sub(
        r"Next domain: \*\*DOM\d{3}\*\* \(.*?\)\.",
        f"Next domain: {next_label}.",
        text,
        count=1,
    )
    PROGRESS.write_text(text, encoding="utf-8")
    print(json.dumps({
        "primary_done": primary,
        "remaining": remaining,
        "domains_left": domains_left,
        "next_domain": next_domain,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
