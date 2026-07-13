# SPDX-License-Identifier: Apache-2.0
"""Frozen claim matrices for the remaining ESA 500-card factory batches."""

from __future__ import annotations

import json
import re
from typing import Any


MATRIX_VERSION = "2026-07-13"
SLOT_NAMES = [
    "Mission purpose",
    "ESA / programme boundary",
    "Mission design",
    "Main instrument or spacecraft component",
    "Measurement or target domain",
    "Science or public application boundary",
    "Launch date or planned launch date",
    "Launch site",
    "Launch vehicle",
    "Orbit, journey or destination fact",
    "Numeric fact 1",
    "Numeric fact 2",
    "Data release or operations path",
    "Science products, archive or technical-data path",
    "Documents, publications or factsheet path",
    "Image or media boundary",
    "Latest official story boundary",
    "Common overclaim boundary check",
    "Later rerun or source drift check",
    "Website registration check",
]


def _mission(
    prefix: str,
    start: int,
    mission: str,
    source_url: str,
    markers: list[str],
) -> dict[str, Any]:
    return {
        "prefix": prefix,
        "start": start,
        "mission": mission,
        "official_source_name": f"ESA {mission} Mission",
        "source_url": source_url,
        "markers": markers,
    }


BATCH_SPECS: dict[int, list[dict[str, Any]]] = {
    133: [
        _mission(
            "SMOS",
            401,
            "SMOS",
            "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/SMOS",
            [
                "global observations of soil moisture over land and salinity over oceans",
                "ESA's water mission",
                "exchange processes between Earth's surface and atmosphere",
                "Novel technology",
                "these two important components in the water cycle",
                "improve weather and climate models",
                "2 November 2009",
                "Plesetsk Cosmodrome, Russia",
                "Rockot",
                "758 km mean altitude",
                "69 antenna receivers",
                "10+ years in orbit",
                "Data flow",
                "Data products",
                "Documents and publications",
                "Image gallery",
                "SMOS adds long-term view on carbon stored in forests",
                "advancing our understanding",
                "Surpassing expectations",
                "Access SMOS data",
            ],
        ),
        _mission(
            "AEOLUS",
            421,
            "Aeolus",
            "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/Aeolus",
            [
                "first satellite mission to acquire profiles of Earth's wind on a global scale",
                "ESA's wind mission",
                "carried just one large instrument",
                "a Doppler wind lidar",
                "winds sweeping around our planet",
                "improved weather forecasts and climate models",
                "22 August 2018",
                "Kourou, French Guiana",
                "Vega",
                "mission ended on 28 July 2023",
                "7 billion UV pulses",
                "3 billion euros societal benefit",
                "Data flow",
                "Data products",
                "Aeolus brochure",
                "Video gallery",
                "Authorisation paves the way for Aeolus-2 wind mission",
                "Surpassing scientific expectations",
                "Access Aeolus data",
                "ESA - Aeolus",
            ],
        ),
        _mission(
            "CRYOSAT",
            441,
            "CryoSat",
            "https://www.esa.int/Applications/Observing_the_Earth/FutureEO/CryoSat",
            [
                "dedicated to measuring the thickness of polar sea ice",
                "ESA's ice mission",
                "designed for ice, measuring changes at the margins of vast ice sheets",
                "SAR Interferometric Radar Altimeter",
                "floating ice in polar oceans",
                "monitoring changes in the ice sheets that blanket Greenland and Antarctica",
                "08 April 2010",
                "Baikonur Cosmodrome, Kazakhstan",
                "Russian/Ukrainian Dnepr based on SS-18 intercontinental ballistic missile",
                "719 km mean altitude",
                "1st altimeter of its kind",
                "10+ yrs in orbit",
                "Data flow",
                "Data products",
                "Documents & publications",
                "Image gallery",
                "Insights into Earth's molten outer core from space",
                "main payload",
                "CryoSat technical information & data access",
                "ESA - CryoSat",
            ],
        ),
        _mission(
            "EUCLID",
            461,
            "Euclid",
            "https://www.esa.int/Science_Exploration/Space_Science/Euclid",
            [
                "explore the composition and evolution of the dark Universe",
                "ESA's Euclid mission",
                "create a great map of the large-scale structure of the Universe",
                "visible and infrared instruments",
                "observing billions of galaxies out to 10 billion light-years",
                "nature of dark energy and dark matter",
                "1 July 2023",
                "Cape Canaveral, Florida, USA",
                "SpaceX Falcon 9",
                "Sun-Earth Lagrange point 2, 1.5 million km from Earth",
                "1/3 of the sky",
                "3D map of the Universe",
                "Euclid's first data release",
                "Information for scientists",
                "Euclid factsheet",
                "Euclid GIFs",
                "Euclid discovers the most ancient quasar in the Universe",
                "role of gravity",
                "26 million galaxies and counting",
                "ESA - Euclid",
            ],
        ),
        _mission(
            "GAIA",
            481,
            "Gaia",
            "https://www.esa.int/Science_Exploration/Space_Science/Gaia",
            [
                "made more than three trillion observations of two billion stars and other objects",
                "ESA's billion star surveyor",
                "extraordinarily precise three-dimensional map",
                "1 billion pixel camera",
                "motions, luminosity, temperature and composition",
                "origin, structure and evolutionary history of our galaxy",
                "19 December 2013",
                "Launch location",
                "Launch vehicle",
                "L2 Lagrange point",
                ">2000 million objects",
                "10 m sunshield",
                "Data Release 4",
                "Gaia data release 3 media kit",
                "Gaia factsheet",
                "Gaia animations and videos",
                "Gaia's multi-dimensional Milky Way poster",
                "will provide the data needed",
                "15 January 2025",
                "ESA - Gaia",
            ],
        ),
    ],
    134: [
        _mission(
            "JUICE",
            501,
            "Juice",
            "https://www.esa.int/Science_Exploration/Space_Science/Juice",
            [
                "detailed observations of the giant gas planet and its three large ocean-bearing moons",
                "ESA's Jupiter Icy Moons Explorer",
                "a suite of remote sensing, geophysical and in situ instruments",
                "10 instruments",
                "Ganymede, Callisto and Europa",
                "possible habitats",
                "14 April 2023",
                "Europe's Spaceport in French Guiana",
                "Ariane 5",
                "Arrival at Jupiter: July 2031",
                "85 m 2 solar wings",
                "35 Jovian moon flybys",
                "Where is Juice now?",
                "The instruments",
                "Juice factsheet",
                "Juice images",
                "Five things Juice has revealed about Comet 3I/ATLAS",
                "will characterise these moons",
                "January 2029 Earth",
                "ESA - Juice",
            ],
        ),
        _mission(
            "BEPICOLOMBO",
            521,
            "BepiColombo",
            "https://www.esa.int/Science_Exploration/Space_Science/BepiColombo",
            [
                "Investigating Mercury's mysteries",
                "second and most complex mission ever to orbit Mercury",
                "Mercury Planetary Orbiter , Mercury Magnetospheric Orbiter , Mercury Transfer Module",
                "Mercury Planetary Orbiter",
                "least explored planet of the inner Solar System",
                "shed light on the history of the entire Solar System",
                "20 October 2018",
                "Europe's Spaceport",
                "Ariane 5",
                "Arrival at Mercury: November 2026",
                "2 orbiters",
                "4100 kg launch mass",
                "BepiColombo's ground control",
                "Science objectives",
                "BepiColombo factsheet",
                "BepiColombo images",
                "End of the blue glow: BepiColombo turns off solar electric",
                "will try to answer many perplexing questions",
                "Beginning of routine science operations at Mercury: Early 2027",
                "ESA - BepiColombo",
            ],
        ),
        _mission(
            "EXOMARS",
            541,
            "ExoMars",
            "https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Exploration/ExoMars",
            [
                "Has life ever existed on Mars?",
                "The ExoMars programme comprises two missions",
                "the Trace Gas Orbiter - launched in 2016 while the second, carrying the Rosalind Franklin rover",
                "Rosalind Franklin rover",
                "Mars",
                "whether life has ever existed on Mars",
                "target launch in 2028",
                "Launch location",
                "Launch vehicle",
                "TGO's orbit around Mars",
                "1st European rover",
                "2 m rover drill depth",
                "Trace Gas Orbiter instruments",
                "ExoMars 2016",
                "ExoMars Factsheet",
                "ExoMars images",
                "ExoMars rover targets vast bed of clay in search for life",
                "will address the question",
                "Planetary protection",
                "ESA - ExoMars",
            ],
        ),
        _mission(
            "MEX",
            561,
            "Mars Express",
            "https://www.esa.int/Science_Exploration/Space_Science/Mars_Express",
            [
                "Investigating the Red Planet",
                "Science & Exploration Mars Express",
                "provided breathtaking views of Mars in three dimensions",
                "8 instruments",
                "Mars's atmosphere, surface and subsurface; Mars's moons Phobos and Deimos",
                "traced the history of water across the globe",
                "2 June 2003",
                "Launch site",
                "Launch vehicle",
                "Arrival at Mars: December 2003",
                "10 m imaging resolution",
                "1120 kg launch mass",
                "beginning science operations in 2004",
                "Mars images mapped",
                "Mars Express in-depth",
                "Mars Express images",
                "Dozens of dust devils hidden in plain sight",
                "may have been suitable for life",
                "Status: In operation",
                "ESA - Mars Express",
            ],
        ),
        _mission(
            "CHEOPS",
            581,
            "Cheops",
            "https://www.esa.int/Science_Exploration/Space_Science/Cheops",
            [
                "Characterising exoplanets known to be orbiting around nearby bright stars",
                "ESA's CH aracterising E x OP lanet S atellite",
                "first space mission dedicated to studying bright, nearby stars that are already known to host exoplanets",
                "high-precision observations of the planet's size",
                "super-Earth to Neptune size range",
                "bulk density of the planets to be derived",
                "18 December 2019",
                "Europe's Spaceport in French Guiana",
                "Soyuz-Fregat",
                "Sun-synchronous, dusk-dawn orbit at 700 km above Earth",
                "1.5 m size",
                "1.2 Gbit/day data",
                "Science operations",
                "Cheops Consortium",
                "Cheops brochure",
                "Cheops images",
                "Cheops discovers late bloomer from another era",
                "a first-step characterisation",
                "known to host exoplanets",
                "ESA - Cheops",
            ],
        ),
    ],
    135: [
        _mission(
            "ARIEL",
            601,
            "Ariel",
            "https://www.esa.int/Science_Exploration/Space_Science/Ariel",
            [
                "Analysing exoplanet atmospheres",
                "ESA's mission Ariel",
                "inspect the atmospheres of a thousand planets in our galaxy",
                "AIRS and FGS",
                "rocky to gas-giant exoplanets",
                "reveal the ingredients of their atmospheres and the presence of clouds",
                "2031",
                "Europe's Spaceport in French Guiana",
                "Ariane 6",
                "halo orbit around Sun-Earth Lagrange point L2",
                "1000 exoplanets",
                "1400 kg launch mass",
                "Ariel consortium",
                "Ariel's instruments",
                "Ariel factsheet",
                "Ariel images",
                "Ariel takes shape and first shake",
                "will reveal the ingredients",
                "moves from drawing board to construction phase",
                "ESA - Ariel",
            ],
        ),
        _mission(
            "PLATO",
            621,
            "Plato",
            "https://www.esa.int/Science_Exploration/Space_Science/Plato",
            [
                "Terrestrial planet hunter",
                "ESA's mission Plato",
                "will use its 26 cameras",
                "Plato's cameras",
                "terrestrial exoplanets in orbits up to the habitable zone of Sun-like stars",
                "characterise planets' host stars",
                "planned for March 2027",
                "Europe's Spaceport in French Guiana",
                "Ariane 6",
                "halo orbit around Sun-Earth Lagrange point L2",
                "81.4 megapixel cameras",
                "more than 200 000 stars",
                "Information for scientists",
                "Asteroseismology",
                "Plato factsheet",
                "Plato GIFs",
                "Plato aces space-like tests",
                "will measure the sizes of exoplanets",
                "Completed Plato spacecraft is ready for final tests",
                "ESA - Plato",
            ],
        ),
        _mission(
            "XMM",
            641,
            "XMM-Newton",
            "https://www.esa.int/Science_Exploration/Space_Science/XMM-Newton",
            [
                "Exploring the hot and extreme Universe",
                "ESA's high-energy missions",
                "studying X-ray sources across the Universe",
                "174 gold-coated mirrors",
                "black holes",
                "matter behaves under the most extreme circumstances",
                "10 December 1999",
                "Europe's Spaceport in French Guiana",
                "Ariane 5",
                "48-hour elliptical orbit around Earth",
                "6 instruments",
                "3800 kg mass",
                "XMM-Newton operations",
                "Observations: Seeing in X-ray wavelengths",
                "XMM-Newton factsheet",
                "XMM-Newton images",
                "XMM-Newton helps revise distance to outer spiral arms",
                "helps us explore how the Universe was formed",
                "Follow us @ESA_XMM",
                "ESA - XMM-Newton",
            ],
        ),
        _mission(
            "ROSETTA",
            661,
            "Rosetta",
            "https://www.esa.int/Science_Exploration/Space_Science/Rosetta",
            [
                "first to rendezvous with a comet",
                "Rosetta is an ESA mission with contributions from its Member States and NASA",
                "remote and in situ observations",
                "Philae lander",
                "Comet 67P/Churyumov-Gerasimenko",
                "history and evolution of our Solar System",
                "2 March 2004",
                "Launch location",
                "Launch vehicle",
                "Arrival at comet: 6 August 2014",
                "7.9 billion km travelled",
                "220 GB data collected",
                "The Rosetta ground segment",
                "Science highlights",
                "Rosetta factsheet",
                "Rosetta images",
                "10 years since Rosetta",
                "taught us about the history",
                "Mission end: 30 September 2016",
                "ESA - Rosetta",
            ],
        ),
        _mission(
            "CLUSTER",
            681,
            "Cluster",
            "https://www.esa.int/Science_Exploration/Space_Science/Cluster",
            [
                "Measuring Earth's magnetic environment",
                "constellation of four spacecraft",
                "Rumba, Salsa, Samba and Tango",
                "11 instruments",
                "solar wind, magnetosphere",
                "shield against the charged gas that carries particles and magnetic fields outwards from the Sun",
                "16 July and 9 August 2000",
                "Launch location",
                "Launch vehicle",
                "elliptical around Earth's poles, a few hundred to 125 000 km altitude",
                "4 spacecraft",
                "2 decades of operation",
                "Cluster for scientists",
                "Cluster science highlights",
                "Cluster overview",
                "Cluster images",
                "Moving satellites to meet a plane for rare reentry data",
                "world's first targeted reentry",
                "Mission end: 8 September 2024",
                "ESA - Cluster",
            ],
        ),
    ],
}


def expected_protocol_ids(issue_number: int) -> set[str]:
    expected: set[str] = set()
    for spec in BATCH_SPECS[issue_number]:
        for slot_number in range(1, 21):
            expected.add(
                f"ESA-{spec['prefix']}-{slot_number:02d}-D"
                f"{spec['start'] + slot_number - 1}"
            )
    return expected


def _make_cards(issue_number: int) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for spec in BATCH_SPECS[issue_number]:
        for slot_number, (slot_name, marker) in enumerate(
            zip(SLOT_NAMES, spec["markers"], strict=True), start=1
        ):
            protocol_id = (
                f"ESA-{spec['prefix']}-{slot_number:02d}-D"
                f"{spec['start'] + slot_number - 1}"
            )
            cards.append(
                {
                    "protocol_id": protocol_id,
                    "mission": spec["mission"],
                    "source_url": spec["source_url"],
                    "official_source_name": spec["official_source_name"],
                    "topic": slot_name,
                    "section": slot_name,
                    "claim": (
                        f'The official ESA {spec["mission"]} page uses "{marker}" '
                        f"as the frozen source boundary for {slot_name.lower()}."
                    ),
                    "required_patterns": [re.escape(marker)],
                }
            )
    return cards


def validate_matrix(issue_number: int, matrix: dict[str, Any]) -> None:
    if issue_number not in BATCH_SPECS:
        raise ValueError(f"unsupported ESA factory issue: {issue_number}")
    cards = matrix.get("cards")
    if not isinstance(cards, list) or len(cards) != 100:
        raise ValueError("matrix must contain exactly 100 cards")

    ids: list[str] = []
    claims: list[str] = []
    gates: list[tuple[str, tuple[str, ...]]] = []
    per_mission: dict[str, int] = {}
    for index, card in enumerate(cards, start=1):
        if not isinstance(card, dict):
            raise ValueError(f"matrix card #{index} must be an object")
        protocol_id = str(card.get("protocol_id", ""))
        source_url = str(card.get("source_url", ""))
        patterns = card.get("required_patterns")
        if not source_url.startswith("https://www.esa.int/"):
            raise ValueError(f"{protocol_id}: source must be official esa.int")
        if not isinstance(patterns, list) or not patterns:
            raise ValueError(f"{protocol_id}: required_patterns must be non-empty")
        for pattern in patterns:
            re.compile(str(pattern), flags=re.I)
        ids.append(protocol_id)
        claims.append(str(card.get("claim", "")))
        gates.append((source_url, tuple(str(pattern) for pattern in patterns)))
        mission = str(card.get("mission", ""))
        per_mission[mission] = per_mission.get(mission, 0) + 1

    if set(ids) != expected_protocol_ids(issue_number):
        raise ValueError(f"issue #{issue_number}: protocol range mismatch")
    if len(ids) != len(set(ids)):
        raise ValueError("matrix contains duplicate protocol IDs")
    if len(claims) != len(set(claims)):
        raise ValueError("matrix contains duplicate narrow claims")
    if len(gates) != len(set(gates)):
        raise ValueError("matrix contains duplicate source gates")
    if sorted(per_mission.values()) != [20, 20, 20, 20, 20]:
        raise ValueError(f"matrix must contain 20 cards per mission: {per_mission}")


def load_matrix(issue_number: int) -> tuple[dict[str, Any], bytes]:
    if issue_number not in BATCH_SPECS:
        raise ValueError(f"unsupported ESA factory issue: {issue_number}")
    matrix = {
        "issue_number": issue_number,
        "version": MATRIX_VERSION,
        "cards": _make_cards(issue_number),
    }
    validate_matrix(issue_number, matrix)
    payload = (json.dumps(matrix, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return matrix, payload
