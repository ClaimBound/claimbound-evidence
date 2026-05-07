#!/usr/bin/env python3
"""Create a draft ClaimBound track scaffold without claiming a result."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_public_benchmarks.scaffold import (  # noqa: E402
    ScaffoldRequest,
    build_scaffold,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--track-type", required=True)
    parser.add_argument(
        "--execution-mode",
        required=True,
        choices=("MANUAL_NO_AI", "AUTOMATED_AI_ASSISTED"),
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source-name", default="Public source under review")
    parser.add_argument("--audience", default="public evidence operators")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    out_dir = args.out
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir

    request = ScaffoldRequest(
        source_url=args.source_url,
        protocol_id=args.protocol_id,
        domain=args.domain,
        track_type=args.track_type,
        execution_mode=args.execution_mode,
        out_dir=out_dir,
        source_name=args.source_name,
        audience=args.audience,
    )
    paths = build_scaffold(request, REPO_ROOT)
    for path in paths:
        print(path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
