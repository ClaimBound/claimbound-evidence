#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run NOAA CO-OPS D-131 frozen pre-registration evaluator over local JSON files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.noaa_coops_fetch import NOAA_COOPS_D131_STATIONS  # noqa: E402
from claimbound_evidence.noaa_coops_prereg_runner import (  # noqa: E402
    build_negative_result_summary,
    evaluate_noaa_coops_prereg,
)

DEFAULT_DOC_PATH = REPO_ROOT / "docs" / "protocols" / "NOAA_COOPS_D131_PREREG_CHARTER.md"


def _manifest_sha256(paths: list[Path]) -> str:
    lines = []
    for path in sorted(paths, key=lambda item: item.name):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    payload = "\n".join(lines) + ("\n" if lines else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", action="append")
    parser.add_argument("--observed", action="append", type=Path)
    parser.add_argument("--predictions", action="append", type=Path)
    parser.add_argument("--raw-dir", type=Path, help="Directory with <station>_observed.json files")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--summary",
        type=Path,
        help="Optional claimbound_negative_result_summary_v1 output path",
    )
    parser.add_argument("--pre-registration-doc", type=Path, default=DEFAULT_DOC_PATH)
    return parser


def _resolve_inputs(args: argparse.Namespace) -> tuple[list[str], list[Path], list[Path]]:
    if args.raw_dir is not None:
        stations = list(args.station or NOAA_COOPS_D131_STATIONS)
        observed = [args.raw_dir / f"{station}_observed.json" for station in stations]
        predictions = [args.raw_dir / f"{station}_predictions.json" for station in stations]
        return stations, observed, predictions

    if not args.station or not args.observed or not args.predictions:
        raise SystemExit("provide --raw-dir or matching --station/--observed/--predictions lists")
    if not (len(args.station) == len(args.observed) == len(args.predictions)):
        raise SystemExit("--station, --observed and --predictions counts must match")
    return list(args.station), list(args.observed), list(args.predictions)


def main() -> int:
    args = _build_parser().parse_args()
    stations, observed_paths, predictions_paths = _resolve_inputs(args)
    for path in observed_paths + predictions_paths:
        if not path.is_file():
            raise SystemExit(f"input file not found: {path}")

    manifest_sha = _manifest_sha256(observed_paths + predictions_paths)
    evaluation = evaluate_noaa_coops_prereg(
        station_ids=stations,
        observed_paths=observed_paths,
        predictions_paths=predictions_paths,
        pre_registration_doc_path=args.pre_registration_doc,
        external_payload_manifest_sha256=manifest_sha,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(evaluation, indent=2, sort_keys=True), encoding="utf-8")
    print(f"report={args.report}")

    if args.summary is not None:
        summary = build_negative_result_summary(evaluation, report_path=args.report)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(f"summary={args.summary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
