# SPDX-License-Identifier: Apache-2.0
"""Tests for the EEA AQ D-001 manual-track runner."""

from __future__ import annotations

import csv
import importlib.util as ilu
import sys
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    script_path = REPO_ROOT / "scripts" / "claimbound_run_eea_manual_track.py"
    spec = ilu.spec_from_file_location("claimbound_run_eea_manual_track_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.START_DATE = date(2024, 1, 1)
    module.END_DATE = date(2024, 1, 10)
    return module


def test_manual_track_passes_when_each_country_has_five_eligible_points(tmp_path: Path) -> None:
    runner = _load_runner()
    csv_path = tmp_path / "eea_sample.csv"
    _write_rows(csv_path, countries=("BE", "DE", "NL"), points_per_country=5)

    summary = runner.build_summary_from_paths(
        [csv_path],
        operator="tester",
        access_date="2026-05-11",
        source_probe=None,
    )

    assert summary["result"]["result_status"] == "PASSED_UNDER_PROTOCOL"
    assert all(item["gate_passed"] for item in summary["by_country"].values())
    assert len(summary["selected_sampling_points"]) == 15


def test_manual_track_records_insufficient_coverage(tmp_path: Path) -> None:
    runner = _load_runner()
    csv_path = tmp_path / "eea_sample.csv"
    _write_rows(csv_path, countries=("BE", "DE"), points_per_country=5)
    _write_rows(csv_path, countries=("NL",), points_per_country=4, append=True)

    summary = runner.build_summary_from_paths(
        [csv_path],
        operator="tester",
        access_date="2026-05-11",
        source_probe=None,
    )

    assert summary["result"]["result_status"] == "INSUFFICIENT_COVERAGE"
    assert summary["by_country"]["NL"]["eligible_sampling_points"] == 4
    assert summary["by_country"]["NL"]["gate_passed"] is False


def test_manual_track_can_write_explicit_blocked_summary() -> None:
    runner = _load_runner()

    summary = runner.build_blocked_summary(
        block_reason="Fixed source manifest was incomplete.",
        operator="tester",
        access_date="2026-05-11",
        source_probe={"probe_type": "fixture"},
    )

    assert summary["result"]["result_status"] == "BLOCKED_SOURCE"
    assert summary["block_reason"] == "Fixed source manifest was incomplete."
    assert summary["raw_payload_policy"] == "Raw EEA payload files stay outside the public repository."


def _write_rows(
    path: Path,
    *,
    countries: tuple[str, ...],
    points_per_country: int,
    append: bool = False,
) -> None:
    fieldnames = [
        "Country",
        "City",
        "SamplingPoint",
        "Pollutant",
        "Start",
        "Value",
        "Unit",
        "AggType",
    ]
    mode = "a" if append else "w"
    with path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        for country in countries:
            for point in range(points_per_country):
                sampling_point = f"SPO.{country}_{country}TEST{point:03d}_PM10"
                for day in _days(date(2024, 1, 1), date(2024, 1, 10)):
                    writer.writerow(
                        {
                            "Country": country,
                            "City": f"{country} City {point:03d}",
                            "SamplingPoint": sampling_point,
                            "Pollutant": "PM10",
                            "Start": day.isoformat(),
                            "Value": "12.5",
                            "Unit": "ug/m3",
                            "AggType": "day",
                        }
                    )


def _days(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)
