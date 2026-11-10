#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build or check read-only static registry views under docs/registry/views/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from claimbound_evidence.registry_view import RegistryViewError, check_views, write_views

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed views are stale; write nothing",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.check:
            problems = check_views(args.root)
            if problems:
                print(
                    "registry views are stale; regenerate with "
                    "scripts/claimbound_build_registry_view.py",
                    file=sys.stderr,
                )
                for p in problems[:50]:
                    print(f"  {p}", file=sys.stderr)
                return 1
            print("registry views are up to date")
            return 0
        names = write_views(args.root)
    except RegistryViewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {len(names)} files to docs/registry/views/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
