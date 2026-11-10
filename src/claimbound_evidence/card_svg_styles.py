# SPDX-License-Identifier: Apache-2.0
"""Inline SVG text styles for GitHub-safe evidence card rendering."""

from __future__ import annotations

import re

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


# Status-chip text is white, so every chip gradient stop must reach this WCAG 2.x
# contrast ratio against it; dark text is checked against the page backgrounds.
MIN_TEXT_CONTRAST = 4.5
CHIP_TEXT_FILL = "#ffffff"
PAGE_BACKGROUNDS = ("#eef3f8", "#ffffff", "#f8fbff", "#fbfcfe")


def style_attr(name: str) -> str:
    try:
        return TEXT_STYLES[name]
    except KeyError as exc:
        raise KeyError(f"unknown SVG text style: {name}") from exc


def gradient_defs() -> list[str]:
    return [
        "  <defs>",
        '    <linearGradient id="greenGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#0b7a70"/>',
        '      <stop offset="100%" stop-color="#08685f"/>',
        "    </linearGradient>",
        '    <linearGradient id="yellowGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#a16207"/>',
        '      <stop offset="100%" stop-color="#854d0e"/>',
        "    </linearGradient>",
        '    <linearGradient id="amberGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#c2410c"/>',
        '      <stop offset="100%" stop-color="#9a3412"/>',
        "    </linearGradient>",
        '    <linearGradient id="redGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#dc2626"/>',
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


def relative_luminance(color: str) -> float:
    """WCAG 2.x relative luminance of a ``#rrggbb`` (or ``#rgb``) colour."""
    value = color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ValueError(f"unsupported colour: {color!r}")
    channels = []
    for index in (0, 2, 4):
        c = int(value[index : index + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.x contrast ratio (1.0 to 21.0) between two colours."""
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def chip_gradient_stops() -> list[str]:
    """Stop colours of the status-chip gradients (not the logo gradients)."""
    stops: list[str] = []
    current = ""
    for line in gradient_defs():
        ident = re.search(r'<linearGradient id="(\w+)"', line)
        if ident:
            current = ident.group(1)
        stop = re.search(r'stop-color="(#[0-9a-fA-F]{6})"', line)
        if stop and current.endswith("Grad") and not current.startswith("logo"):
            stops.append(stop.group(1))
    return stops


def text_color_pairs() -> list[tuple[str, str, str, float]]:
    """All (style, foreground, background, ratio) text pairs the renderer emits."""
    pairs: list[tuple[str, str, str, float]] = []
    for name, attrs in TEXT_STYLES.items():
        match = re.search(r'fill="(#[0-9a-fA-F]{6})"', attrs)
        if match is None:
            continue
        fg = match.group(1)
        backgrounds = (
            chip_gradient_stops() if fg.lower() == CHIP_TEXT_FILL else list(PAGE_BACKGROUNDS)
        )
        pairs.extend((name, fg, bg, contrast_ratio(fg, bg)) for bg in backgrounds)
    return pairs
