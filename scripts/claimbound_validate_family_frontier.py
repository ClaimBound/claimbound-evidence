#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate a ClaimBound R&D family frontier JSON file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.family_ledger import (  # noqa: E402
    load_frontier_ledger,
    validate_frontier_ledger,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frontier", type=Path)
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Optional base directory for context capsule and tombstone path checks.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    base_dir = args.base_dir or args.frontier.parent
    frontier = load_frontier_ledger(args.frontier)
    violations = validate_frontier_ledger(frontier, base_dir)
    if violations:
        for violation in violations:
            print(f"violation: {violation}", file=sys.stderr)
        return 1
    print(f"valid_frontier_ledger={args.frontier}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
