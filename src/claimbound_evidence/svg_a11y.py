# SPDX-License-Identifier: Apache-2.0
"""Static accessibility lint for ClaimBound SVG files.

This is a structural and colour-contrast heuristic, not a WCAG conformance
audit. See ``docs/ACCESSIBILITY.md`` for what is and is not checked.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from claimbound_evidence.card_svg_styles import (
    MIN_TEXT_CONTRAST,
    PAGE_BACKGROUNDS,
    contrast_ratio,
)

_SVG_NS = "{http://www.w3.org/2000/svg}"
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_URL_RE = re.compile(r"url\(#([^)]+)\)")


def lint_svg_text(svg: str) -> list[str]:
    """Return accessibility findings for one SVG document (empty list = clean).

    Findings are stable strings without file-specific values so callers can
    count them by kind.
    """
    try:
        root = ET.fromstring(svg.encode("utf-8"))
    except ET.ParseError:
        return ["svg is not well-formed XML"]

    if root.tag != f"{_SVG_NS}svg":
        return ["root element is not <svg>"]

    findings: list[str] = []
    if root.get("role") != "img":
        findings.append('root <svg> lacks role="img"')

    elements = {el.get("id"): el for el in root.iter() if el.get("id")}
    labelled = (root.get("aria-labelledby") or "").split()
    if not labelled:
        findings.append("root <svg> lacks aria-labelledby")
    kinds: set[str] = set()
    for ident in labelled:
        el = elements.get(ident)
        if el is None:
            findings.append("aria-labelledby references a missing id")
        elif el.tag in (f"{_SVG_NS}title", f"{_SVG_NS}desc") and "".join(el.itertext()).strip():
            kinds.add(el.tag.removeprefix(_SVG_NS))
    for kind in ("title", "desc"):
        if kind not in kinds:
            findings.append(f"no non-empty <{kind}> referenced by aria-labelledby")

    findings.extend(_contrast_findings(root))
    return findings


def _contrast_findings(root: ET.Element) -> list[str]:
    stops: dict[str, list[str]] = {}
    for grad in root.iter(f"{_SVG_NS}linearGradient"):
        ident = grad.get("id")
        if ident:
            stops[ident] = [
                s.get("stop-color", "")
                for s in grad.iter(f"{_SVG_NS}stop")
                if _HEX_RE.match(s.get("stop-color", ""))
            ]
    used: set[str] = set()
    for rect in root.iter(f"{_SVG_NS}rect"):
        match = _URL_RE.fullmatch(rect.get("fill", ""))
        if match and match.group(1) in stops and not match.group(1).startswith("logo"):
            used.add(match.group(1))
    chip_stops = [color for ident in sorted(used) for color in stops[ident]]

    logo_text = {
        id(text)
        for group in root.iter(f"{_SVG_NS}g")
        if "logo" in group.get("aria-label", "").lower()
        for text in group.iter(f"{_SVG_NS}text")
    }  # logotypes are exempt from contrast requirements (WCAG 1.4.3)

    findings: list[str] = []
    for text in root.iter(f"{_SVG_NS}text"):
        fill = text.get("fill", "")
        if id(text) in logo_text or not _HEX_RE.match(fill):
            continue
        backgrounds = chip_stops if fill.lower() == "#ffffff" else list(PAGE_BACKGROUNDS)
        if any(contrast_ratio(fill, bg) < MIN_TEXT_CONTRAST for bg in backgrounds):
            finding = f"text contrast below {MIN_TEXT_CONTRAST}:1"
            if finding not in findings:
                findings.append(finding)
    return findings


def lint_svg_file(path: Path) -> list[str]:
    return lint_svg_text(path.read_text(encoding="utf-8"))
