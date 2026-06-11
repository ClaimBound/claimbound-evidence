# SPDX-License-Identifier: Apache-2.0
"""Inline SVG text styles for GitHub-safe evidence card rendering."""

from __future__ import annotations

WIDTH = 2000
HEIGHT = 1190

_FONT = 'font-family="Inter, Segoe UI, Arial, sans-serif"'
_MONO = 'font-family="SFMono-Regular, Consolas, Liberation Mono, monospace"'

TEXT_STYLES: dict[str, str] = {
    "title": f'{_FONT} font-size="50" font-weight="750" fill="#0d1736"',
    "subtitle": f'{_FONT} font-size="23" font-weight="400" fill="#55627a"',
    "chipLabel": f'{_FONT} font-size="16" font-weight="650" fill="#536174"',
    "chipText": f'{_FONT} font-size="21" font-weight="800" fill="#ffffff"',
    "claimLabel": f'{_FONT} font-size="20" font-weight="750" fill="#1758d6"',
    "claimText": f'{_FONT} font-size="39" font-weight="800" fill="#0d1736"',
    "fieldLabel": f'{_FONT} font-size="19" font-weight="750" fill="#1758d6"',
    "fieldText": f'{_FONT} font-size="22" font-weight="600" fill="#111827"',
    "mono": f'{_MONO} font-size="18" font-weight="600" fill="#111827"',
    "bodyText": f'{_FONT} font-size="20" font-weight="500" fill="#1f2937"',
    "muted": f'{_FONT} font-size="17" font-weight="500" fill="#55627a"',
}


def style_attr(name: str) -> str:
    try:
        return TEXT_STYLES[name]
    except KeyError as exc:
        raise KeyError(f"unknown SVG text style: {name}") from exc


def gradient_defs() -> list[str]:
    return [
        "  <defs>",
        '    <linearGradient id="greenGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#0fbaaa"/>',
        '      <stop offset="100%" stop-color="#0a9f93"/>',
        "    </linearGradient>",
        '    <linearGradient id="yellowGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#fbbf24"/>',
        '      <stop offset="100%" stop-color="#d97706"/>',
        "    </linearGradient>",
        '    <linearGradient id="amberGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#f97316"/>',
        '      <stop offset="100%" stop-color="#c2410c"/>',
        "    </linearGradient>",
        '    <linearGradient id="redGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#ef4444"/>',
        '      <stop offset="100%" stop-color="#b91c1c"/>',
        "    </linearGradient>",
        '    <linearGradient id="grayGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#64748b"/>',
        '      <stop offset="100%" stop-color="#475569"/>',
        "    </linearGradient>",
        '    <linearGradient id="blueGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#1f64f2"/>',
        '      <stop offset="100%" stop-color="#1758d6"/>',
        "    </linearGradient>",
        '    <linearGradient id="logoRingBlue" x1="73" y1="453" x2="348" y2="793" gradientUnits="userSpaceOnUse">',
        '      <stop offset="0" stop-color="#1E64BA"/>',
        '      <stop offset="0.55" stop-color="#0C75C8"/>',
        '      <stop offset="1" stop-color="#0A5FAB"/>',
        "    </linearGradient>",
        '    <linearGradient id="logoRingTeal" x1="221" y1="792" x2="403" y2="594" gradientUnits="userSpaceOnUse">',
        '      <stop offset="0" stop-color="#18B7A3"/>',
        '      <stop offset="1" stop-color="#089EBC"/>',
        "    </linearGradient>",
        '    <linearGradient id="logoSignalGradient" x1="61" y1="628" x2="404" y2="628" gradientUnits="userSpaceOnUse">',
        '      <stop offset="0" stop-color="#1E64BA"/>',
        '      <stop offset="0.43" stop-color="#0877C4"/>',
        '      <stop offset="0.72" stop-color="#0A97BB"/>',
        '      <stop offset="1" stop-color="#14B69E"/>',
        "    </linearGradient>",
        "  </defs>",
    ]


def result_gradient(result_status: str) -> str:
    value = result_status.upper()
    if value in {"PASSED_UNDER_PROTOCOL", "REPRODUCED_OUTCOME"}:
        return "greenGrad"
    if value == "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT":
        return "yellowGrad"
    if value in {"BLOCKED_SOURCE", "INSUFFICIENT_COVERAGE"}:
        return "amberGrad"
    if value == "NEGATIVE_RESULT_UNDER_PROTOCOL":
        return "redGrad"
    if "DRAFT" in value or "NOT_EXECUTED" in value:
        return "grayGrad"
    return "blueGrad"


def validity_gradient(card_validity_level: str) -> str:
    value = card_validity_level.upper()
    if value.startswith("GREEN") or value == "VALIDATED":
        return "greenGrad"
    if value.startswith("YELLOW"):
        return "yellowGrad"
    if value.startswith("RED"):
        return "redGrad"
    if value.startswith("GRAY") or "DRAFT" in value:
        return "grayGrad"
    return "blueGrad"


def reproduction_gradient(reproduction_level: str) -> str:
    value = reproduction_level.upper()
    if value == "REPRODUCED_OUTCOME":
        return "greenGrad"
    if "SOURCE_BYTE_DRIFT" in value or "BYTE DRIFT" in value:
        return "yellowGrad"
    if "NOT" in value and "REPRODUCED" in value:
        return "blueGrad"
    if "DRAFT" in value or "NOT_EXECUTED" in value:
        return "grayGrad"
    return "blueGrad"
