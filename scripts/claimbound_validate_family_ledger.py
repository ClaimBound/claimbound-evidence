#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate a ClaimBound R&D family ledger JSON file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_public_benchmarks.family_ledger import (  # noqa: E402
    load_family_ledger,
    validate_family_ledger,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    ledger = load_family_ledger(args.ledger)
    violations = validate_family_ledger(ledger)
    if violations:
        for violation in violations:
            print(f"violation: {violation}", file=sys.stderr)
        return 1
    print(f"valid_family_ledger={args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
