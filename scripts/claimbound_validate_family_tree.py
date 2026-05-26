#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate a ClaimBound protocol v3 tree overlay JSON file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.tree_overlay import (  # noqa: E402
    load_tree_overlay,
    validate_tree_overlay,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    tree = load_tree_overlay(args.tree)
    violations = validate_tree_overlay(tree)
    if violations:
        for violation in violations:
            print(f"violation: {violation}", file=sys.stderr)
        return 1
    print(f"valid_tree_overlay={args.tree}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
