#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fetch NOAA CO-OPS D-131 official JSON payloads into a local directory.

NOAA limits hourly_height requests to 365 days. This helper downloads frozen
D-131 scope in yearly chunks and merges payloads outside the repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.noaa_coops_fetch import (  # noqa: E402
    NOAA_COOPS_D131_BEGIN,
    NOAA_COOPS_D131_END,
    NOAA_COOPS_D131_STATIONS,
    fetch_d131_station_payloads,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Local directory outside the repository for merged JSON payloads.",
    )
    parser.add_argument(
        "--station",
        action="append",
        default=[],
        help=f"Station id; default all D-131 stations: {', '.join(NOAA_COOPS_D131_STATIONS)}",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    stations = tuple(args.station or NOAA_COOPS_D131_STATIONS)
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for station in stations:
        paths = fetch_d131_station_payloads(station, out_dir)
        for path in paths:
            print(path.as_posix())

    print(
        "scope="
        f"{NOAA_COOPS_D131_BEGIN.isoformat()}..{NOAA_COOPS_D131_END.isoformat()} "
        f"stations={','.join(stations)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
