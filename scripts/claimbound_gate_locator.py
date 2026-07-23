#!/usr/bin/env python3
"""Conservative, gate-aware verbatim locator extraction for public claim batches."""
from __future__ import annotations

import re
from dataclasses import dataclass

SPACE = re.compile(r"\s+")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?(?:\s*%|\s+per\s+\d+)?\b", re.I)

GATE_TERMS: dict[str, tuple[re.Pattern[str], ...]] = {
    "source-integrity": (
        re.compile(r"\b(?:official|agency|department|commission|organization|programme|program|report|data|dataset)\b", re.I),
    ),
    "numerator-denominator": (
        re.compile(r"\b(?:percent|percentage|rate|ratio|total|number|per\s+\d+|denominator|sample)\b", re.I),
    ),
    "coverage": (
        re.compile(r"\b(?:coverage|scope|population|geograph|region|area|includes?|excludes?|eligible|observations?)\b", re.I),
    ),
    "time-boundary": (
        YEAR,
        re.compile(r"\b(?:date|period|annual|monthly|daily|since|between|during|updated|published)\b", re.I),
    ),
    "method-version": (
        re.compile(r"\b(?:method|methodology|version|standard|protocol|procedure|classification|calibrat|model)\b", re.I),
    ),
    "comparator": (
        re.compile(r"\b(?:baseline|compar|reference|control|versus|relative to|change from|trend)\b", re.I),
    ),
    "reproducibility": (
        re.compile(r"\b(?:download|api|dataset|data available|methodology|documentation|code|repository|access tool)\b", re.I),
    ),
    "negative-evidence": (
        re.compile(r"\b(?:limit|uncertain|error|fail|loss|risk|adverse|missing|gap|violation|caveat|bias)\w*\b", re.I),
        re.compile(r"\b(?:may|might|cannot|incomplete|subject to)\b", re.I),
    ),
    "conflicts-disclosure": (
        re.compile(r"\b(?:published by|prepared by|managed by|responsible|agency|department|commission|organization|authority)\b", re.I),
    ),
    "overclaim-drift": (
        re.compile(r"\b(?:limit|uncertain|may|might|can|cannot|does not|not necessarily|subject to|estimate)\w*\b", re.I),
    ),
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


def _sentences(text: str) -> list[str]:
    cleaned = SPACE.sub(" ", text.replace("\x00", " ")).strip()
    return [
        sentence.strip(" \t\r\n-•")
        for sentence in re.split(r"(?<=[.!?])\s+|\s*[|]\s*", cleaned)
        if 24 <= len(sentence.strip()) <= 700
    ]


def _topic_terms(topic: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.findall(r"[a-z0-9]+", topic.casefold())
        if len(token) >= 4 and token not in STOPWORDS
    )


def locate_gate(text: str, topic: str, gate: str) -> LocatorDecision:
    """Return one verbatim sentence only when it supports the named gate."""
    patterns = GATE_TERMS[gate]
    terms = _topic_terms(topic)
    candidates: list[tuple[int, str]] = []
    for sentence in _sentences(text):
        folded = sentence.casefold()
        topic_hits = sum(term in folded for term in terms)
        gate_hits = sum(bool(pattern.search(sentence)) for pattern in patterns)
        if not gate_hits:
            continue
        if gate == "numerator-denominator" and not NUMBER.search(sentence):
            continue
        # A topic-specific term is required where one exists. This prevents a
        # generic footer, navigation element, or unrelated institutional line
        # from becoming a pass.
        if terms and topic_hits == 0:
            continue
        score = topic_hits * 10 + gate_hits * 3 - max(0, len(sentence) - 280) // 40
        candidates.append((score, sentence))
    if not candidates:
        return LocatorDecision(None, "No topic-specific sentence satisfied the gate predicate.")
    locator = max(candidates, key=lambda item: item[0])[1]
    return LocatorDecision(locator, "A topic-specific verbatim sentence satisfied the gate predicate.")


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
