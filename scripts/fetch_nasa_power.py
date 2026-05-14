#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Materialize NASA POWER D-103 solar series into the generic OHLCV CSV contract.

Supported source modes:

* ``mock``: deterministic synthetic daily solar-resource series for offline tests only.
* ``nasa_power_json_file``: parse an operator-supplied local NASA POWER Daily
  JSON file. No network I/O occurs in this script.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_public_benchmarks.generic_ohlcv_batch_pre_registration_meta import (  # noqa: E402
    build_generic_ohlcv_batch_reproducibility,
)
from claimbound_public_benchmarks.nasa_power import (  # noqa: E402
    NASA_POWER_POINTS,
    NasaPowerMockConfig,
    build_nasa_power_dataset_id,
    generate_nasa_power_mock_daily_series,
    normalize_point_id,
    parse_nasa_power_json_file,
    solar_7d_mean_from_values,
    write_nasa_power_manifest,
    write_nasa_power_solar_ohlcv_csv,
)


def _parse_date(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("date must not be empty")
    return date.fromisoformat(text)


def _default_out_path(point_id: str, start: date, end: date, mode: str) -> Path:
    pid = normalize_point_id(point_id)
    stem = f"nasa_power_{pid.lower()}_{start.isoformat()}_{end.isoformat()}_{mode}"
    return REPO_ROOT / "data" / "research_runs" / "nasa_power" / f"{stem}.csv"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--point",
        required=True,
        help=f"NASA POWER point id; one of: {', '.join(sorted(NASA_POWER_POINTS))}",
    )
    parser.add_argument(
        "--mode",
        default="mock",
        choices=("mock", "nasa_power_json_file"),
        help="Source mode (default: mock).",
    )
    parser.add_argument("--start", default=None, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD.")
    parser.add_argument("--seed", type=int, default=None, help="Optional mock seed.")
    parser.add_argument(
        "--json-path",
        type=Path,
        default=None,
        help="Local NASA POWER Daily JSON (json_file mode).",
    )
    parser.add_argument("--out", type=Path, default=None, help="Output OHLCV CSV path.")
    parser.add_argument(
        "--dataset-id",
        default=None,
        help="Override dataset_id (default derived from point and mode).",
    )
    return parser


def _resolve_series(args: argparse.Namespace) -> tuple[list[date], object, date, date]:
    point_id = normalize_point_id(args.point)
    if args.mode == "mock":
        if args.start is None or args.end is None:
            raise ValueError("mock mode requires --start and --end")
        start = _parse_date(args.start)
        end = _parse_date(args.end)
        config = NasaPowerMockConfig(
            point_id=point_id, start=start, end=end, seed=args.seed
        )
        days, values = generate_nasa_power_mock_daily_series(config)
        return days, values, days[0], days[-1]
    if args.mode == "nasa_power_json_file":
        if args.json_path is None:
            raise ValueError("nasa_power_json_file mode requires --json-path")
        days, values, _summary = parse_nasa_power_json_file(args.json_path)
        return days, values, days[0], days[-1]
    raise ValueError(f"unsupported mode {args.mode!r}")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    point_id = normalize_point_id(args.point)
    days, values, start, end = _resolve_series(args)
    solar_7d_mean = solar_7d_mean_from_values(values)

    out_path = args.out or _default_out_path(point_id, start, end, args.mode)
    csv_path = write_nasa_power_solar_ohlcv_csv(days, solar_7d_mean, out_path)
    dataset_id = args.dataset_id or build_nasa_power_dataset_id(
        point_id, source_mode=args.mode
    )
    repro = build_generic_ohlcv_batch_reproducibility()
    manifest_path = write_nasa_power_manifest(
        csv_path,
        dataset_id=dataset_id,
        point_id=point_id,
        source_mode=args.mode,
        start_date=start,
        end_date=end,
        rows=len(days),
        repo_semver=repro.get("repo_semver") if isinstance(repro, dict) else None,
        git_commit_short=repro.get("git_commit_short") if isinstance(repro, dict) else None,
    )
    print(f"point={point_id}")
    print(f"mode={args.mode}")
    print(f"dataset_id={dataset_id}")
    print(f"rows={len(days)}")
    print(f"ohlcv_csv={csv_path}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
