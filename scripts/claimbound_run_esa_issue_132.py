#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the frozen ESA issue #132 100-card batch locally."""

from __future__ import annotations

import argparse
import json
import sys

from esa_issue_132_common import sha256_bytes
from esa_issue_132_data import load_matrix
from esa_issue_132_preview import run_preview
from esa_issue_132_publish import run_publish


def _check(_args: argparse.Namespace) -> int:
    matrix, payload = load_matrix()
    print(f"matrix_cards={len(matrix['cards'])}")
    print(f"matrix_sha256={sha256_bytes(payload)}")
    print("matrix_status=VALID")
    return 0


def _preview(args: argparse.Namespace) -> int:
    return run_preview(run_root_arg=args.run_root, quiet=args.quiet)


def _publish(args: argparse.Namespace) -> int:
    return run_publish(
        preview_arg=args.preview,
        operator=args.operator,
        confirm_reviewed=args.confirm_reviewed,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Validate the frozen 100-card matrix.")
    check.set_defaults(func=_check)

    preview = subparsers.add_parser(
        "preview",
        help="Fetch five ESA pages and write a local-only frozen preview.",
    )
    preview.add_argument(
        "--run-root",
        help="Optional new local run directory; default is under ~/claimbound_runs/.",
    )
    preview.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the preview path, useful for shell capture.",
    )
    preview.set_defaults(func=_preview)

    publish = subparsers.add_parser(
        "publish",
        help="Create missing evidence cards from a reviewed frozen preview.",
    )
    publish.add_argument("--preview", required=True, help="Local preview.json path.")
    publish.add_argument("--operator", required=True, help="Operator handle.")
    publish.add_argument(
        "--confirm-reviewed",
        action="store_true",
        help="Confirm that the frozen preview was reviewed before publication.",
    )
    publish.set_defaults(func=_publish)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
