#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Lint SVG files for basic accessibility (report-only unless --strict)."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.svg_a11y import lint_svg_file  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=REPO_ROOT / "docs", type=Path)
    parser.add_argument("--strict", action="store_true", help="exit 1 if any finding exists")
    parser.add_argument("--list", action="store_true", help="print findings per file")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    files = sorted(args.root.rglob("*.svg"))
    kinds: Counter[str] = Counter()
    failing = 0
    for path in files:
        findings = lint_svg_file(path)
        failing += bool(findings)
        for finding in findings:
            kinds[finding] += 1
            if args.list:
                print(f"{path}: {finding}")
    print(f"svg_files={len(files)} clean={len(files) - failing} with_findings={failing}")
    for kind, count in sorted(kinds.items()):
        print(f"finding[{count}]: {kind}")
    return 1 if args.strict and failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
