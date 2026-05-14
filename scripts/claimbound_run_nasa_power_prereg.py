#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run NASA POWER D-103 frozen pre-registration evaluator over local JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_public_benchmarks.nasa_power_prereg_runner import (  # noqa: E402
    evaluate_nasa_power_prereg,
)

DEFAULT_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "protocols"
    / "NASA_POWER_D103_PREREG_CHARTER.md"
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--point", action="append", required=True)
    parser.add_argument("--json", action="append", required=True, type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--pre-registration-doc", type=Path, default=DEFAULT_DOC_PATH)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if len(args.point) != len(args.json):
        raise SystemExit("--point and --json counts must match")
    for path in args.json:
        if not path.is_file():
            raise SystemExit(f"input file not found: {path}")
    evaluation = evaluate_nasa_power_prereg(
        point_ids=list(args.point),
        json_paths=list(args.json),
        pre_registration_doc_path=args.pre_registration_doc,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(evaluation, indent=2, sort_keys=True), encoding="utf-8")
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
