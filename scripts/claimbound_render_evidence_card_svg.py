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
WIDTH = 2200
HEIGHT = 1660


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
        "      .title{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:66px;font-weight:700;fill:#0d1736}",
        "      .subtitle{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:30px;font-weight:400;fill:#55627a}",
        "      .wordmark{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:52px;font-weight:800;fill:#082f59}",
        "      .wordmark2{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:52px;font-weight:800;fill:#117fc5}",
        "      .smallcaps{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:22px;font-weight:700;fill:#55627a}",
        "      .chipLabel{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:20px;font-weight:600;fill:#536174;text-transform:uppercase}",
        "      .chipText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:25px;font-weight:800;fill:#ffffff}",
        "      .claimLabel{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:24px;font-weight:700;fill:#1758d6}",
        "      .claimText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:50px;font-weight:800;fill:#0d1736}",
        "      .fieldLabel{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:24px;font-weight:700;fill:#1758d6}",
        "      .fieldText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:28px;font-weight:600;fill:#111827}",
        "      .mono{font-family:SFMono-Regular,Consolas,'Liberation Mono',monospace;font-size:23px;font-weight:600;fill:#111827}",
        "      .bodyText{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:25px;font-weight:500;fill:#1f2937}",
        "      .muted{font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:22px;font-weight:500;fill:#55627a}",
        "    </style>",
        '    <linearGradient id="okGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#0fbaaa"/>',
        '      <stop offset="100%" stop-color="#0a9f93"/>',
        "    </linearGradient>",
        '    <linearGradient id="blueGrad" x1="0" y1="0" x2="1" y2="0">',
        '      <stop offset="0%" stop-color="#1f64f2"/>',
        '      <stop offset="100%" stop-color="#1758d6"/>',
        "    </linearGradient>",
        "  </defs>",
        f'  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#eef3f8"/>',
        f'  <rect x="44" y="44" width="{WIDTH - 88}" height="{HEIGHT - 88}" rx="34" fill="#ffffff" stroke="#cfd7e3" stroke-width="3"/>',
        '  <path d="M80 191 H2120" stroke="#d7dde7" stroke-width="3"/>',
        '  <text x="86" y="103" class="wordmark">Claim</text>',
        '  <text x="228" y="103" class="wordmark2">Bound</text>',
        '  <text x="88" y="142" class="smallcaps">PUBLIC BENCHMARKS</text>',
        '  <text x="620" y="111" class="title">ClaimBound Evidence Card</text>',
        '  <text x="624" y="157" class="subtitle">Protocol-bound, reproducible evidence summary</text>',
    ]

    out.extend(
        _chip(86, 225, 470, "Result status", values["result_status"], "okGrad")
    )
    out.extend(
        _chip(586, 225, 430, "Validity", values["card_validity_level"], "okGrad")
    )
    out.extend(
        _chip(1046, 225, 440, "Reproduction", values["reproduction_level"], "blueGrad")
    )
    out.extend(
        _chip(1516, 225, 570, "Record type", values["record_type"], "blueGrad")
    )

    out.extend(_claim_box(86, 335, 2028, values["allowed_claim_sentence"]))

    x1, x2 = 86, 1104
    w = 982
    out.extend(_field_box(x1, 540, w, 150, "Evidence ID", values["evidence_id"], mono=True))
    out.extend(_field_box(x2, 540, w, 150, "Protocol", values["protocol_id"], mono=True))
    out.extend(_field_box(x1, 720, w, 170, "Official Source", values["source"]))
    out.extend(_field_box(x2, 720, w, 170, "Target / Candidate", f"{values['target_definition']}\n{values['candidate_definition']}"))
    out.extend(_field_box(x1, 920, w, 170, "Controls / Gate", values["controls_and_gate"]))
    out.extend(_field_box(x2, 920, w, 170, "Period / Scope / Date", f"{values['period_scope']}\nAccess date: {values['access_date']}"))
    out.extend(_field_box(x1, 1120, w, 170, "Artifact / Report", f"{values['artifact_ref']}\n{values['sanitized_report_path']}"))
    out.extend(_field_box(x2, 1120, w, 170, "Evidence URL", values["evidence_url"], mono=True))

    out.extend(
        _wide_note(
            86,
            1310,
            2028,
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
        f'  <rect x="{x}" y="{y}" width="{w}" height="70" rx="24" fill="url(#{gradient_id})"/>',
    ]
    text_lines = _wrap(value, _chars_for_width(w - 54, 25), max_lines=2)
    start_y = y + 31 if len(text_lines) == 2 else y + 44
    lines.extend(_text_lines(x + 27, start_y, text_lines, "chipText", 30))
    return lines


def _claim_box(x: int, y: int, w: int, claim: str) -> list[str]:
    lines = [
        f'  <rect x="{x}" y="{y}" width="{w}" height="155" rx="22" fill="#f8fbff" stroke="#1758d6" stroke-width="4"/>',
        f'  <text x="{x + 34}" y="{y + 44}" class="claimLabel">Allowed narrow claim</text>',
    ]
    wrapped = _wrap(claim, _chars_for_width(w - 68, 50), max_lines=2)
    lines.extend(_text_lines(x + 34, y + 103, wrapped, "claimText", 57))
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
    font_size = 23 if mono else 28
    line_height = 31 if mono else 34
    max_lines = max(1, (h - 64) // line_height)
    wrapped = _wrap(value, _chars_for_width(w - 52, font_size), max_lines=max_lines)

    lines = [
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="#d8dee9" stroke-width="3"/>',
        f'  <text x="{x + 26}" y="{y + 37}" class="fieldLabel">{_e(label)}</text>',
    ]
    lines.extend(_text_lines(x + 26, y + 76, wrapped, text_class, line_height))
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
    boundary_lines = _wrap(boundary, _chars_for_width(w - 60, 25), max_lines=3)
    limitation_text = " Limitations: " + " ".join(f"{idx + 1}. {item}" for idx, item in enumerate(limitations))
    limitation_lines = _wrap(limitation_text, _chars_for_width(w - 60, 22), max_lines=2)
    h = 58 + (len(boundary_lines) * 31) + 18 + (len(limitation_lines) * 27) + 34

    lines = [
        f'  <rect x="{x}" y="{y - 2}" width="{w}" height="{h}" rx="14" fill="#fbfcfe" stroke="#d8dee9" stroke-width="3"/>',
        f'  <text x="{x + 28}" y="{y + 33}" class="fieldLabel">{_e(label)}</text>',
    ]
    lines.extend(_text_lines(x + 28, y + 70, boundary_lines, "bodyText", 31))
    lines.extend(_text_lines(x + 28, y + 70 + len(boundary_lines) * 31 + 15, limitation_lines, "muted", 27))
    return lines


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
