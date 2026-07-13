# SPDX-License-Identifier: Apache-2.0
"""Frozen claim matrix for ClaimBound issue #132."""

from __future__ import annotations

import json
import re
from typing import Any


MATRIX_VERSION = "2026-07-13"
ISSUE_NUMBER = 132
SLOT_NAMES = [
    "Mission purpose",
    "ESA / programme boundary",
    "Mission design",
    "Main instrument",
    "Measurement domain",
    "Public application boundary",
    "Launch date or planned launch date",
    "Launch site",
    "Launch vehicle",
    "Orbit / altitude / destination fact",
    "Numeric fact 1",
    "Numeric fact 2",
    "Data flow or operations path",
    "Data products or technical-data path",
    "Documents / publications / mission-kit path",
    "Image / media boundary",
    "Latest official story boundary",
    "Common overclaim boundary check",
    "Later rerun / source drift check",
    "Website registration check",
]


MISSION_SPECS: list[dict[str, Any]] = [
    {
        "prefix": "S6",
        "start": 301,
        "mission": "Sentinel-6",
        "official_source_name": "ESA Sentinel-6 Mission",
        "source_url": "https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-6",
        "facts": {
            "purpose": "charting sea level for Copernicus",
            "boundary": "the next radar altimetry reference mission",
            "design": "each satellite carries a Poseidon-4 radar altimeter and a microwave radiometer",
            "instrument": "a Poseidon-4 radar altimeter",
            "measurement": "sea-surface height measurements",
            "application": "global mean sea level rising because of climate change",
            "launch_date": "Sentinel-6 Michael Freilich - 21 November 2020",
            "launch_site": "Vandenberg, California, US",
            "launch_vehicle": "SpaceX Falcon 9",
            "orbit": "1336 km orbit altitude",
            "numeric_1": "3.2 mm yearly sea-level rise",
            "numeric_2": "66° orbit inclination",
            "operations": "Eumetsat takes control of Sentinel-6B",
            "data_products": "Documents and publications",
            "docs": "Sentinel-6 mission kit",
            "media": "Image gallery",
            "latest_story": "First image from Sentinel-6B extends sea-level legacy 16/12/2025",
            "overclaim": "Documents and publications",
            "rerun": "Latest",
            "website": "Sentinel-6",
        },
    },
    {
        "prefix": "ECARE",
        "start": 321,
        "mission": "EarthCARE",
        "official_source_name": "ESA EarthCARE Mission",
        "source_url": "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/EarthCARE",
        "facts": {
            "purpose": "ESA's cloud and aerosol mission",
            "boundary": "Earth Cloud Aerosol and Radiation Explorer",
            "design": "equipped with four instruments",
            "instrument": "the Earth Cloud Aerosol and Radiation Explorer (EarthCARE) satellite mission",
            "measurement": "clouds and aerosols play in regulating Earth's climate",
            "application": "regulating Earth's climate",
            "launch_date": "29 May 2024",
            "launch_site": "Vandenberg, California, US",
            "launch_vehicle": "SpaceX Falcon 9",
            "orbit": "393 km altitude",
            "numeric_1": "21 sq m solar panel",
            "numeric_2": "4 instruments",
            "operations": "EarthCARE operations and data processing",
            "data_products": "EarthCARE data products",
            "docs": "EarthCARE mission kit",
            "media": "EarthCARE images",
            "latest_story": "A first: EarthCARE cloud data sharpen weather forecasts 25/06/2026",
            "overclaim": "EarthCARE mission kit",
            "rerun": "EarthCARE documents and publications",
            "website": "EarthCARE",
        },
    },
    {
        "prefix": "BIOMASS",
        "start": 341,
        "mission": "Biomass",
        "official_source_name": "ESA Biomass Mission",
        "source_url": "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/Biomass",
        "facts": {
            "purpose": "ESA's forest mission",
            "boundary": "the Biomass mission",
            "design": "carrying a novel P-band synthetic aperture radar",
            "instrument": "a novel P-band synthetic aperture radar",
            "measurement": "crucial information about the state of our forests",
            "application": "role forests play in the carbon cycle",
            "launch_date": "29 April 2025",
            "launch_site": "Kourou, French Guiana",
            "launch_vehicle": "Vega-C",
            "orbit": "666 km altitude",
            "numeric_1": "1st P-band radar in space",
            "numeric_2": "1250 kg mass",
            "operations": "Biomass is now in space - what happens next?",
            "data_products": "Documents and publications",
            "docs": "Biomass mission kit",
            "media": "Biomass images",
            "latest_story": "ESA's Biomass goes live with data now open to all 26/01/2026",
            "overclaim": "Biomass mission kit",
            "rerun": "Documents and publications",
            "website": "Biomass",
        },
    },
    {
        "prefix": "FLEX",
        "start": 361,
        "mission": "FLEX",
        "official_source_name": "ESA FLEX Mission",
        "source_url": "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/FLEX",
        "facts": {
            "purpose": "ESA's photosynthesis mission",
            "boundary": "the Fluorescence Explorer (FLEX)",
            "design": "using novel technology",
            "instrument": "the Fluorescence Explorer (FLEX)",
            "measurement": "information about the health of the world's plants",
            "application": "how carbon moves between plants and the atmosphere and how photosynthesis affects the carbon and water cycles",
            "launch_date": "September 2026",
            "launch_site": "Kourou, French Guiana",
            "launch_vehicle": "Vega-C",
            "orbit": "814 Km altitude",
            "numeric_1": "3.5 yrs mission life",
            "numeric_2": "27-day repeat cycle",
            "operations": "FLEX and Sentinel-3C head to launch site",
            "data_products": "Data products",
            "docs": "Documents and publications",
            "media": "FLEX images",
            "latest_story": "Three ESA-built satellites on show in France 16/04/2026",
            "overclaim": "FLEX and Sentinel-3C head to launch site",
            "rerun": "Documents and publications",
            "website": "FLEX",
        },
    },
    {
        "prefix": "SWARM",
        "start": 381,
        "mission": "Swarm",
        "official_source_name": "ESA Swarm Mission",
        "source_url": "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/Swarm",
        "facts": {
            "purpose": "ESA's magnetic field mission",
            "boundary": "three-satellite Swarm mission is dedicated to unravelling",
            "design": "ESA's three-satellite Swarm mission",
            "instrument": "1st sensors of their kind",
            "measurement": "the magnetic field and electric currents in and around Earth",
            "application": "weather in space caused by solar activity",
            "launch_date": "22 November 2013",
            "launch_site": "Plesetsk Cosmodrome, Russia",
            "launch_vehicle": "Rockot",
            "orbit": "1st Explorer constellation",
            "numeric_1": "3 identical satellites",
            "numeric_2": "1st sensors of their kind",
            "operations": "Data flow",
            "data_products": "Data products",
            "docs": "Documents and publications",
            "media": "Image gallery",
            "latest_story": "Insights into Earth's molten outer core from space 21/05/2026",
            "overclaim": "weather in space caused by solar activity",
            "rerun": "Discover Swarm",
            "website": "Swarm",
        },
    },
]


def _escape(value: str) -> str:
    return re.escape(value)


def _make_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for mission_spec in MISSION_SPECS:
        facts = mission_spec["facts"]
        for slot_number, slot_name in enumerate(SLOT_NAMES, start=1):
            protocol_id = (
                f"ESA-{mission_spec['prefix']}-{slot_number:02d}-D"
                f"{mission_spec['start'] + slot_number - 1}"
            )
            card = {
                "protocol_id": protocol_id,
                "mission": mission_spec["mission"],
                "source_url": mission_spec["source_url"],
                "official_source_name": mission_spec["official_source_name"],
                "topic": slot_name,
                "section": slot_name,
                "claim": _claim_text(mission_spec["mission"], slot_name, facts),
                "required_patterns": _required_patterns(slot_number, facts),
            }
            cards.append(card)
    return cards


def _claim_text(mission: str, slot_name: str, facts: dict[str, str]) -> str:
    if slot_name == "Mission purpose":
        return f"The official ESA {mission} page states {facts['purpose']}."
    if slot_name == "ESA / programme boundary":
        return f"The official ESA {mission} page keeps the mission within {facts['boundary']}."
    if slot_name == "Mission design":
        return f"The official ESA {mission} page describes {facts['design']}."
    if slot_name == "Main instrument":
        return f"The official ESA {mission} page names {facts['instrument']}."
    if slot_name == "Measurement domain":
        return f"The official ESA {mission} page focuses on {facts['measurement']}."
    if slot_name == "Public application boundary":
        return f"The official ESA {mission} page limits the public application story to {facts['application']}."
    if slot_name == "Launch date or planned launch date":
        return f"The official ESA {mission} page gives launch timing as {facts['launch_date']}."
    if slot_name == "Launch site":
        return f"The official ESA {mission} page lists {facts['launch_site']} as the launch site."
    if slot_name == "Launch vehicle":
        return f"The official ESA {mission} page lists {facts['launch_vehicle']} as the launcher."
    if slot_name == "Orbit / altitude / destination fact":
        return f"The official ESA {mission} page gives {facts['orbit']}."
    if slot_name == "Numeric fact 1":
        return f"The official ESA {mission} page states {facts['numeric_1']}."
    if slot_name == "Numeric fact 2":
        return f"The official ESA {mission} page states {facts['numeric_2']}."
    if slot_name == "Data flow or operations path":
        return f"The official ESA {mission} page highlights {facts['operations']}."
    if slot_name == "Data products or technical-data path":
        return f"The official ESA {mission} page links to {facts['data_products']}."
    if slot_name == "Documents / publications / mission-kit path":
        return f"The official ESA {mission} page exposes {facts['docs']}."
    if slot_name == "Image / media boundary":
        return f"The official ESA {mission} page includes {facts['media']}."
    if slot_name == "Latest official story boundary":
        return f"The official ESA {mission} page shows {facts['latest_story']}."
    if slot_name == "Common overclaim boundary check":
        return f"The official ESA {mission} page should not be read beyond {facts['overclaim']}."
    if slot_name == "Later rerun / source drift check":
        return f"The official ESA {mission} page leaves a {facts['rerun']} for reruns and drift checks."
    if slot_name == "Website registration check":
        return f"The official ESA {mission} page can be registered as {facts['website']}."
    raise ValueError(f"unknown slot name: {slot_name}")


def _required_patterns(slot_number: int, facts: dict[str, str]) -> list[str]:
    key_map = {
        1: [facts["purpose"]],
        2: [facts["boundary"]],
        3: [facts["design"]],
        4: [facts["instrument"]],
        5: [facts["measurement"]],
        6: [facts["application"]],
        7: [facts["launch_date"]],
        8: [facts["launch_site"]],
        9: [facts["launch_vehicle"]],
        10: [facts["orbit"]],
        11: [facts["numeric_1"]],
        12: [facts["numeric_2"]],
        13: [facts["operations"]],
        14: [facts["data_products"]],
        15: [facts["docs"]],
        16: [facts["media"]],
        17: [facts["latest_story"]],
        18: [facts["overclaim"]],
        19: [facts["rerun"]],
        20: [facts["website"]],
    }
    return [_escape(pattern) for pattern in key_map[slot_number]]


def expected_protocol_ids() -> set[str]:
    expected: set[str] = set()
    for mission_spec in MISSION_SPECS:
        for slot_number in range(1, 21):
            expected.add(
                f"ESA-{mission_spec['prefix']}-{slot_number:02d}-D"
                f"{mission_spec['start'] + slot_number - 1}"
            )
    return expected


def validate_matrix(matrix: dict[str, Any]) -> None:
    cards = matrix.get("cards")
    if not isinstance(cards, list) or len(cards) != 100:
        raise ValueError("matrix must contain exactly 100 cards")

    ids: list[str] = []
    claims: list[str] = []
    per_mission: dict[str, int] = {}

    for index, card in enumerate(cards, start=1):
        if not isinstance(card, dict):
            raise ValueError(f"matrix card #{index} must be an object")
        required = {
            "protocol_id",
            "mission",
            "source_url",
            "official_source_name",
            "topic",
            "section",
            "claim",
            "required_patterns",
        }
        missing = sorted(required - set(card))
        if missing:
            raise ValueError(f"matrix card #{index} missing: {', '.join(missing)}")

        protocol_id = str(card["protocol_id"])
        source_url = str(card["source_url"])
        claim = str(card["claim"])
        patterns = card["required_patterns"]

        if not source_url.startswith("https://www.esa.int/"):
            raise ValueError(f"{protocol_id}: source must be official esa.int")
        if not isinstance(patterns, list) or not patterns:
            raise ValueError(f"{protocol_id}: required_patterns must be non-empty")
        for pattern in patterns:
            re.compile(str(pattern), flags=re.I)

        ids.append(protocol_id)
        claims.append(claim)
        mission = str(card["mission"])
        per_mission[mission] = per_mission.get(mission, 0) + 1

    if len(ids) != len(set(ids)):
        raise ValueError("matrix contains duplicate protocol IDs")
    expected = expected_protocol_ids()
    if set(ids) != expected:
        missing = sorted(expected - set(ids))
        extra = sorted(set(ids) - expected)
        raise ValueError(
            f"matrix protocol range mismatch; missing={missing}, extra={extra}"
        )
    if len(claims) != len(set(claims)):
        raise ValueError("matrix contains duplicate narrow claims")
    if sorted(per_mission.values()) != [20, 20, 20, 20, 20]:
        raise ValueError(
            f"matrix must contain 20 cards per mission: {per_mission}"
        )


def load_matrix() -> tuple[dict[str, Any], bytes]:
    cards = _make_cards()
    matrix = {
        "issue_number": ISSUE_NUMBER,
        "version": MATRIX_VERSION,
        "cards": cards,
    }
    validate_matrix(matrix)
    payload = (json.dumps(matrix, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    return matrix, payload
