#!/usr/bin/env python3
"""Render a readable ClaimBound evidence-card SVG from JSON."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


DEFAULT_TEMPLATE = Path("docs/assets/claimbound_evidence_card.svg")
WIDTH = 2000
HEIGHT = 1190


def render_svg(card_path: Path, template_path: Path = DEFAULT_TEMPLATE) -> str:
    """Render an SVG card.

    The template argument is kept for CLI compatibility with older runbooks.
    This renderer now uses a built-in responsive SVG layout because the old
    placeholder template could only safely display one-line values.
    """

    del template_path
    card = json.loads(card_path.read_text(encoding="utf-8"))
    if not isinstance(card, dict):
        raise ValueError("evidence card must be a JSON object")

    return _render_card(_visual_values(card))


def _visual_values(card: dict[str, Any]) -> dict[str, Any]:
    visual = card.get("visual_summary")
    if not isinstance(visual, dict):
        visual = {}

    evidence_id = str(card.get("evidence_id", ""))
    source_name = str(card.get("official_source_name", ""))
    source_url = str(card.get("official_source_url", ""))
    sanitized_report_path = str(card.get("sanitized_report_path", ""))
    sanitized_report_sha256 = str(card.get("sanitized_report_sha256", ""))

    return {
        "access_date": str(card.get("access_date", "")),
        "allowed_claim_sentence": _first(
            visual,
            "allowed_claim_sentence",
            card.get("allowed_claim_sentence") or card.get("claim_type"),
        ),
        "artifact_ref": _first(visual, "artifact_ref", sanitized_report_path),
        "candidate_definition": _first(visual, "candidate_definition", source_name),
        "card_validity_level": str(card.get("card_validity_level", "VALIDATED")),
        "claim_boundary": str(card.get("claim_boundary", "")),
        "controls_and_gate": _first(
            visual,
            "controls_and_gate",
            card.get("baseline_control_summary"),
        ),
        "evidence_id": evidence_id,
        "evidence_url": _format_path(
            _first(visual, "evidence_url", f"docs/evidence_cards/{evidence_id}.json")
        ),
        "known_limitations": [str(item) for item in card.get("known_limitations", [])],
        "operator": str(card.get("operator", "")),
        "period_scope": _first(visual, "period_scope", card.get("access_date")),
        "protocol_id": str(card.get("protocol_id", "")),
        "raw_payload_policy": str(
            card.get("raw_payload_manifest") or card.get("source_rights_note") or ""
        ),
        "record_type": str(card.get("record_type", "")),
        "reproduction_level": _short_reproduction(str(card.get("reproduction_level", ""))),
        "result_status": str(card.get("result_status", "")),
        "sanitized_report_path": sanitized_report_path,
        "sanitized_report_sha256": sanitized_report_sha256,
        "source": f"{source_name}\n{source_url}".strip(),
        "target_definition": _first(visual, "target_definition", card.get("domain")),
    }


def _render_card(values: dict[str, Any]) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
            'aria-label="ClaimBound Evidence Card">'
        ),
        "  <defs>",
        "    <style>",
        "      .title{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:50px;font-weight:750;fill:#0d1736}",
        "      .subtitle{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:23px;font-weight:400;fill:#55627a}",
        "      .chipLabel{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:16px;font-weight:650;fill:#536174;text-transform:uppercase}",
        "      .chipText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:21px;font-weight:800;fill:#ffffff}",
        "      .claimLabel{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:20px;font-weight:750;fill:#1758d6}",
        "      .claimText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:39px;font-weight:800;fill:#0d1736}",
        "      .fieldLabel{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:19px;font-weight:750;fill:#1758d6}",
        "      .fieldText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:22px;font-weight:600;fill:#111827}",
        "      .mono{font-family:SFMono-Regular,Consolas,'Liberation Mono',monospace;font-size:18px;font-weight:600;fill:#111827}",
        "      .bodyText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:20px;font-weight:500;fill:#1f2937}",
        "      .muted{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:17px;font-weight:500;fill:#55627a}",
        "    </style>",
        '    <linearGradient id="okGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#0fbaaa"/>',
        '      <stop offset="100%" stop-color="#0a9f93"/>',
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
        f'  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#eef3f8"/>',
        f'  <rect x="44" y="44" width="{WIDTH - 88}" height="{HEIGHT - 88}" rx="34" fill="#ffffff" stroke="#cfd7e3" stroke-width="3"/>',
        '  <path d="M70 158 H1930" stroke="#d7dde7" stroke-width="3"/>',
        '  <text x="70" y="93" class="title">ClaimBound Evidence Card</text>',
        '  <text x="73" y="129" class="subtitle">Protocol-bound, reproducible evidence summary</text>',
        *(_logo_lockup(1415, 52, 0.33)),
    ]

    out.extend(
        _chip(70, 193, 430, "Result status", values["result_status"], "okGrad")
    )
    out.extend(
        _chip(520, 193, 370, "Validity", values["card_validity_level"], "okGrad")
    )
    out.extend(
        _chip(910, 193, 480, "Reproduction", values["reproduction_level"], "blueGrad")
    )
    out.extend(
        _chip(1410, 193, 520, "Record type", values["record_type"], "blueGrad")
    )

    out.extend(_claim_box(70, 278, 1860, values["allowed_claim_sentence"]))

    x1, x2 = 70, 1010
    w = 920
    out.extend(_field_box(x1, 420, w, 106, "Evidence ID", values["evidence_id"], mono=True))
    out.extend(_field_box(x2, 420, w, 106, "Protocol", values["protocol_id"], mono=True))
    out.extend(_field_box(x1, 542, w, 114, "Official Source", values["source"]))
    out.extend(_field_box(x2, 542, w, 114, "Target / Candidate", f"{values['target_definition']}\n{values['candidate_definition']}"))
    out.extend(_field_box(x1, 672, w, 114, "Controls / Gate", values["controls_and_gate"]))
    out.extend(_field_box(x2, 672, w, 114, "Period / Scope / Date", f"{values['period_scope']}\nAccess date: {values['access_date']}"))
    out.extend(_field_box(x1, 802, w, 114, "Artifact / Report", f"{values['artifact_ref']}\n{values['sanitized_report_path']}"))
    out.extend(_field_box(x2, 802, w, 114, "Evidence URL", values["evidence_url"], mono=True))

    out.extend(
        _wide_note(
            70,
            938,
            1860,
            "Claim boundary",
            values["claim_boundary"],
            values["known_limitations"],
        )
    )

    out.append("</svg>")
    return "\n".join(out) + "\n"


def _chip(x: int, y: int, w: int, label: str, value: str, gradient_id: str) -> list[str]:
    lines = [
        f'  <text x="{x}" y="{y - 18}" class="chipLabel">{_e(label)}</text>',
        f'  <rect x="{x}" y="{y}" width="{w}" height="52" rx="17" fill="url(#{gradient_id})"/>',
    ]
    text_lines = _wrap(value, _chars_for_width(w - 42, 21), max_lines=2)
    start_y = y + 23 if len(text_lines) == 2 else y + 34
    lines.extend(_text_lines(x + 21, start_y, text_lines, "chipText", 24))
    return lines


def _claim_box(x: int, y: int, w: int, claim: str) -> list[str]:
    lines = [
        f'  <rect x="{x}" y="{y}" width="{w}" height="96" rx="16" fill="#f8fbff" stroke="#1758d6" stroke-width="4"/>',
        f'  <text x="{x + 26}" y="{y + 31}" class="claimLabel">Allowed narrow claim</text>',
    ]
    wrapped = _wrap(claim, _chars_for_width(w - 52, 39), max_lines=2)
    lines.extend(_text_lines(x + 26, y + 73, wrapped, "claimText", 42))
    return lines


def _field_box(
    x: int,
    y: int,
    w: int,
    h: int,
    label: str,
    value: str,
    *,
    mono: bool = False,
) -> list[str]:
    text_class = "mono" if mono else "fieldText"
    font_size = 18 if mono else 22
    line_height = 23 if mono else 26
    max_lines = max(1, (h - 48) // line_height)
    wrapped = _wrap(value, _chars_for_width(w - 52, font_size), max_lines=max_lines)

    lines = [
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="#d8dee9" stroke-width="3"/>',
        f'  <text x="{x + 22}" y="{y + 29}" class="fieldLabel">{_e(label)}</text>',
    ]
    lines.extend(_text_lines(x + 22, y + 58, wrapped, text_class, line_height))
    return lines


def _wide_note(
    x: int,
    y: int,
    w: int,
    label: str,
    boundary: str,
    limitations: list[str],
) -> list[str]:
    h = 0
    boundary_lines = _wrap(boundary, _chars_for_width(w - 48, 20), max_lines=3)
    limitation_text = " Limitations: " + " ".join(f"{idx + 1}. {item}" for idx, item in enumerate(limitations))
    limitation_lines = _wrap(limitation_text, _chars_for_width(w - 48, 17), max_lines=2)
    h = 42 + (len(boundary_lines) * 24) + 10 + (len(limitation_lines) * 20) + 22

    lines = [
        f'  <rect x="{x}" y="{y - 2}" width="{w}" height="{h}" rx="14" fill="#fbfcfe" stroke="#d8dee9" stroke-width="3"/>',
        f'  <text x="{x + 22}" y="{y + 28}" class="fieldLabel">{_e(label)}</text>',
    ]
    lines.extend(_text_lines(x + 22, y + 55, boundary_lines, "bodyText", 24))
    lines.extend(_text_lines(x + 22, y + 55 + len(boundary_lines) * 24 + 10, limitation_lines, "muted", 20))
    return lines


def _logo_lockup(x: int, y: int, scale: float) -> list[str]:
    return [
        f'  <g aria-label="ClaimBound public benchmarks logo" transform="translate({x},{y}) scale({scale}) translate(-40,-478)">',
        '    <g stroke-linecap="butt" stroke-linejoin="round">',
        '      <g stroke="#CBD3DC" stroke-width="3.2" stroke-linecap="round" stroke-dasharray="10 12" opacity="0.72">',
        '        <path d="M130 507V714"/>',
        '        <path d="M162 490V719"/>',
        '        <path d="M199 491V719"/>',
        '        <path d="M230 471V726"/>',
        '        <path d="M276 521V690"/>',
        '        <path d="M327 508V650"/>',
        '        <path d="M128 520H277"/>',
        '        <path d="M128 595H327"/>',
        '        <path d="M128 672H355"/>',
        "      </g>",
        '      <path d="M342.6 514.3A160 160 0 1 0 230 787" fill="none" stroke="url(#logoRingBlue)" stroke-width="23"/>',
        '      <path d="M230 787A160 160 0 0 0 388.4 649.3" fill="none" stroke="url(#logoRingTeal)" stroke-width="23"/>',
        '      <path d="M63 629.5C87 616.4 104.3 613.6 121.2 632.2C140.7 653.8 153.4 651.6 162.1 616.2C173.8 568.5 182.5 527.5 198.9 527.5C217.5 527.5 228.4 590.6 240.3 630.8C253.4 675.4 268.6 682.8 284.6 641.5C303.5 592.9 315.2 567.6 333.7 574.7C352.6 582 355.7 635.1 376.6 634.9C386.2 634.8 394 630.4 402 626.8" fill="none" stroke="url(#logoSignalGradient)" stroke-width="11.5" stroke-linecap="round"/>',
        '      <path d="M284 684.5L307.5 707.7L353 657" fill="none" stroke="#12B4A4" stroke-width="10.5" stroke-linecap="square"/>',
        "    </g>",
        '    <text x="428" y="633" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="124" font-weight="750" fill="#082F59" text-rendering="geometricPrecision">Claim</text>',
        '    <text x="792" y="633" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="124" font-weight="750" fill="#0E73CC" text-rendering="geometricPrecision">Bound</text>',
        '    <line x1="436" y1="700" x2="514" y2="700" stroke="#11AFA9" stroke-width="4"/>',
        '    <text x="542" y="717" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="38" font-weight="500" letter-spacing="13" fill="#082F59">public benchmarks</text>',
        '    <line x1="1120" y1="700" x2="1194" y2="700" stroke="#11AFA9" stroke-width="4"/>',
        "  </g>",
    ]


def _text_lines(x: int, y: int, lines: list[str], class_name: str, line_height: int) -> list[str]:
    return [
        f'  <text x="{x}" y="{y + idx * line_height}" class="{class_name}">{_e(line)}</text>'
        for idx, line in enumerate(lines)
    ]


def _wrap(value: str, width: int, *, max_lines: int) -> list[str]:
    paragraphs = [
        " ".join(part.split())
        for part in str(value or "").splitlines()
        if part.strip()
    ]
    if not paragraphs:
        return ["n/a"]

    lines: list[str] = []
    for paragraph in paragraphs:
        lines.extend(
            textwrap.wrap(
                paragraph,
                width=max(8, width),
                break_long_words=True,
                break_on_hyphens=False,
            )
        )
    return lines[:max_lines]


def _chars_for_width(width: int, font_size: int) -> int:
    return max(8, int(width / (font_size * 0.55)))


def _first(mapping: dict[str, Any], key: str, fallback: object) -> str:
    value = mapping.get(key)
    if value is None or str(value).strip() == "":
        value = fallback
    return str(value or "")


def _format_path(value: str) -> str:
    if len(value) <= 64 or "/" not in value:
        return value
    prefix, leaf = value.rsplit("/", 1)
    return f"{prefix}/\n{leaf}"


def _short_reproduction(value: str) -> str:
    value = value.strip()
    if value.lower() == "not independently reproduced":
        return "not independently reproduced"
    return value


def _e(value: str) -> str:
    return escape(str(value), {'"': "&quot;"})


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    svg = render_svg(args.card, args.template)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    print(f"rendered_svg={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
