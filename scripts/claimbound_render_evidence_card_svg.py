#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Render a readable ClaimBound evidence-card SVG from JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

from claimbound_evidence.card_svg_render import render_all_cards, render_svg


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path, nargs="?")
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate every docs/evidence_cards/CLAIMBOUND-*.json SVG sibling.",
    )
    parser.add_argument(
        "--cards-dir",
        type=Path,
        default=Path("docs/evidence_cards"),
        help="Directory containing evidence-card JSON files.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.all:
        rendered = render_all_cards(args.cards_dir)
        for path in rendered:
            print(f"rendered_svg={path}")
        return 0

    if args.card is None or args.output is None:
        raise SystemExit("card and output paths are required unless --all is set")

    svg = render_svg(args.card)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    print(f"rendered_svg={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
