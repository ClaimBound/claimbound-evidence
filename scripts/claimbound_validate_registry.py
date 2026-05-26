#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the ClaimBound public evidence registry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.registry import (  # noqa: E402
    load_registry,
    validate_registry,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "registry",
        default=REPO_ROOT / "docs" / "registry" / "evidence_index.json",
        nargs="?",
        type=Path,
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    registry = load_registry(args.registry)
    violations = validate_registry(registry, REPO_ROOT)
    if violations:
        for violation in violations:
            print(f"violation: {violation}", file=sys.stderr)
        return 1
    print(f"valid_registry={args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
