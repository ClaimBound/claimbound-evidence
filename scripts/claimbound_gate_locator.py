#!/usr/bin/env python3
"""Conservative, gate-aware verbatim locator extraction for public claim batches."""
from __future__ import annotations

import re
from dataclasses import dataclass

SPACE = re.compile(r"\s+")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?(?:\s*%|\s+per\s+\d+)?\b", re.I)

GATE_FACETS: dict[str, tuple[re.Pattern[str], ...]] = {
    "source-integrity": (
        re.compile(r"\b(?:official|agency|department|commission|organization|programme|program|report|data|dataset)\b", re.I),
    ),
    "numerator-denominator": (
        NUMBER,
        re.compile(r"\b(?:numerator|cases?|events?|count|number)\b", re.I),
        re.compile(r"\b(?:denominator|total|sample|population|out of|per\s+\d+)\b", re.I),
        re.compile(r"(?:%|\bpercent(?:age)?\b|\brate\b|\bratio\b|\bunits?\b)", re.I),
        re.compile(r"\b(?:exclud|missing|unknown|not included)\w*\b", re.I),
        re.compile(r"\b(?:round|precision|decimal place)\w*\b", re.I),
    ),
    "coverage": (
        re.compile(r"\b(?:population|people|participants?|patients?|species|facilities|sites?|observations?)\b", re.I),
        re.compile(r"\b(?:geograph|region|area|country|countries|state|states|national|global|scope)\w*\b", re.I),
        re.compile(r"\b(?:includes?|eligible|criteria|scope)\b", re.I),
        re.compile(r"\b(?:missing|unreported|unknown|incomplete)\w*\b", re.I),
        re.compile(r"\b(?:limit|exclud|not covered|does not cover)\w*\b", re.I),
    ),
    "time-boundary": (
        re.compile(r"\b(?:19|20)\d{2}\b|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", re.I),
        re.compile(r"\b(?:date|period|annual|monthly|daily|since|between|during|from|through|updated|published|year)\b", re.I),
    ),
    "method-version": (
        re.compile(r"\b(?:method|methodology|standard|protocol|procedure|classification|model)\w*\b", re.I),
        re.compile(r"\b(?:version|software|revision|release)\w*\b", re.I),
        re.compile(r"\bthresholds?\b", re.I),
        re.compile(r"\b(?:transform|adjust|normaliz|calibrat)\w*\b", re.I),
        re.compile(r"\b(?:quality control|validation|verification)\b", re.I),
    ),
    "comparator": (
        re.compile(r"\b(?:baseline|compar|reference|control|versus|relative to|change from|trend)\b", re.I),
        re.compile(r"\b(?:population|participants?|patients?|sample|cohort)\b", re.I),
        re.compile(r"\b(?:condition|setting|scenario|operating)\w*\b", re.I),
        re.compile(r"\b(?:period|year|window|from|through|between)\b", re.I),
        re.compile(r"\b(?:method|measure|metric|definition|units?)\w*\b", re.I),
    ),
    "reproducibility": (
        re.compile(r"\b(?:download|api|dataset|data available|repository|access tool)\b", re.I),
        re.compile(r"\b(?:methodology|documentation|code|procedure|protocol|instructions?)\b", re.I),
    ),
    "negative-evidence": (
        re.compile(r"\b(?:limit|uncertain|error|fail|loss|risk|adverse|missing|gap|violation|caveat|bias)\w*\b", re.I),
        re.compile(r"\b(?:may|might|cannot|incomplete|subject to)\b", re.I),
    ),
    "conflicts-disclosure": (
        re.compile(r"\b(?:sponsor|vendor|author|owner|funder|contractor|agency|department|commission|organization|authority)\w*\b", re.I),
        re.compile(
            r"\b(?:conflicts? of interest|financial disclosure|funded by|"
            r"fund" r"ing (?:was )?provided by|sponsored by|contracted by|"
            r"supported by|no conflicts?)\b",
            re.I,
        ),
    ),
    "overclaim-drift": (
        re.compile(r"\b(?:may|might|cannot|does not|not necessarily|subject to)\b", re.I),
        re.compile(r"\b(?:limit|uncertain|estimate|risk|vary|incomplete|assumption)\w*\b", re.I),
    ),
}

GATE_FACET_NAMES: dict[str, tuple[str, ...]] = {
    "source-integrity": ("official-source-boundary",),
    "numerator-denominator": (
        "numeric-value",
        "numerator",
        "denominator",
        "units-or-rate",
        "exclusions-or-missingness",
        "rounding-rule",
    ),
    "coverage": (
        "population",
        "geography",
        "inclusion-rules",
        "missingness",
        "coverage-limits",
    ),
    "time-boundary": ("date-or-period", "temporal-applicability"),
    "method-version": (
        "method",
        "software-or-version",
        "thresholds",
        "transformations-or-calibration",
        "quality-controls",
    ),
    "comparator": (
        "baseline",
        "population",
        "operating-condition",
        "time-window",
        "measurement-rule",
    ),
    "reproducibility": ("public-input-access", "rerun-procedure"),
    "negative-evidence": ("adverse-or-limiting-evidence", "explicit-qualification"),
    "conflicts-disclosure": ("responsible-or-interested-party", "interest-or-support-disclosure"),
    "overclaim-drift": ("explicit-qualification", "limitation-or-uncertainty"),
}

STOPWORDS = {
    "about", "after", "before", "between", "data", "from", "into", "more",
    "quality", "rate", "report", "service", "services", "system", "than",
    "that", "their", "these", "this", "through", "under", "with",
}


@dataclass(frozen=True)
class LocatorDecision:
    locator: str | None
    basis: str
    missing_facets: tuple[str, ...] = ()


def _sentences(text: str) -> list[str]:
    candidates: list[str] = []
    for raw_line in text.replace("\x00", " ").splitlines():
        line = SPACE.sub(" ", raw_line).strip(" \t\r\n-•")
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+|\s*[|]\s*", line)
        if len(parts) == 1 and 24 <= len(line) <= 700:
            candidates.append(line)
        else:
            candidates.extend(part.strip(" \t\r\n-•") for part in parts if 24 <= len(part.strip()) <= 700)
    return candidates


def _topic_terms(topic: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.findall(r"[a-z0-9]+", topic.casefold())
        if len(token) >= 4 and token not in STOPWORDS
    )


def locate_gate(text: str, topic: str, gate: str) -> LocatorDecision:
    """Return one verbatim sentence only when it supports the named gate."""
    facets = GATE_FACETS[gate]
    terms = _topic_terms(topic)
    facet_candidates: list[list[tuple[int, str]]] = [[] for _ in facets]
    for sentence in _sentences(text):
        folded = sentence.casefold()
        topic_hits = sum(term in folded for term in terms)
        # A topic-specific term is required where one exists. This prevents a
        # generic footer, navigation element, or unrelated institutional line
        # from becoming a pass.
        if terms and topic_hits == 0:
            continue
        total_facet_hits = sum(bool(facet.search(sentence)) for facet in facets)
        for index, facet in enumerate(facets):
            if facet.search(sentence):
                score = topic_hits * 10 + total_facet_hits * 3 - max(0, len(sentence) - 280) // 40
                facet_candidates[index].append((score, sentence))
    missing = tuple(
        name
        for name, candidates in zip(GATE_FACET_NAMES[gate], facet_candidates, strict=True)
        if not candidates
    )
    if missing:
        return LocatorDecision(
            None,
            "The frozen source did not satisfy every required gate facet.",
            missing,
        )
    selected = [max(candidates, key=lambda item: item[0])[1] for candidates in facet_candidates]
    locator = " || ".join(dict.fromkeys(selected))
    return LocatorDecision(locator, "Topic-specific verbatim sentences satisfied every required gate facet.")


def build_locator_matrix(
    sources: dict[str, str],
    claims: list[dict[str, object]],
) -> dict[str, dict[str, str]]:
    """Build a sparse source/gate matrix; missing gates remain insufficient."""
    matrix: dict[str, dict[str, str]] = {}
    for claim in claims:
        key = f"{claim['domain_code']}-T{int(claim['topic_index']):02d}"
        decision = locate_gate(sources[key], str(claim["topic"]), str(claim["gate"]))
        if decision.locator:
            matrix.setdefault(key, {})[str(claim["gate"])] = decision.locator
    return matrix
