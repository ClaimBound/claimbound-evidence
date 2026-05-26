#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate a ClaimBound evidence-card JSON file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.evidence_card import (  # noqa: E402
    load_evidence_card,
    validate_evidence_card,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    card = load_evidence_card(args.card)
    violations = validate_evidence_card(card)
    if violations:
        for violation in violations:
            print(f"violation: {violation}", file=sys.stderr)
        return 1
    print(f"valid_evidence_card={args.card}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
