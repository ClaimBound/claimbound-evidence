# SPDX-License-Identifier: Apache-2.0
"""Offline tests for NOAA CO-OPS D-131 prereg runner."""

from __future__ import annotations

import importlib.util as ilu
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from claimbound_evidence.baseline_groups import Doc11AcceptanceConfig
from claimbound_evidence.noaa_coops_prereg_runner import (
    NOAA_COOPS_NEGATIVE_SUMMARY_SCHEMA,
    NOAA_COOPS_PREREG_REPORT_SCHEMA,
    NoaaCoopsPreregConfig,
    build_negative_result_summary,
    evaluate_noaa_coops_prereg,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_station_pair(
    directory: Path,
    station: str,
    *,
    hours: int,
    phase: float,
) -> tuple[Path, Path]:
    start = datetime(2018, 1, 1)
    observed_rows = []
    prediction_rows = []
    for hour in range(hours):
        ts = start + timedelta(hours=hour)
        stamp = ts.strftime("%Y-%m-%d %H:%M")
        seasonal = np.sin((hour + phase) / 24.0)
        tide = 1.5 * seasonal
        observed = tide + (0.4 if hour % 97 == 0 else 0.0)
        prediction = tide
        observed_rows.append({"t": stamp, "v": f"{observed:.6f}"})
        prediction_rows.append({"t": stamp, "v": f"{prediction:.6f}"})
    observed_path = directory / f"{station}_observed.json"
    predictions_path = directory / f"{station}_predictions.json"
    observed_path.write_text(json.dumps({"data": observed_rows}), encoding="utf-8")
    predictions_path.write_text(json.dumps({"predictions": prediction_rows}), encoding="utf-8")
    return observed_path, predictions_path


def _load_cli_module():
    script_path = REPO_ROOT / "scripts" / "claimbound_run_noaa_coops_prereg.py"
    spec = ilu.spec_from_file_location("pb_run_noaa_coops_prereg_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_noaa_coops_prereg_runner_report_shape(tmp_path: Path) -> None:
    stations = ["8518750", "9414290", "8638610"]
    observed_paths = []
    predictions_paths = []
    for idx, station in enumerate(stations):
        observed, predictions = _write_station_pair(
            tmp_path,
            station,
            hours=4 * 365 * 24,
            phase=float(idx),
        )
        observed_paths.append(observed)
        predictions_paths.append(predictions)

    cfg = NoaaCoopsPreregConfig(
        train_hours=2 * 365 * 24,
        test_hours=365 * 24,
        step_hours=365 * 24,
        minimum_test_event_count=1,
        min_joined_rows=1000,
        acceptance=Doc11AcceptanceConfig(
            top_rate=0.10,
            min_windows=2,
            min_positive_rate=0.65,
            min_event_rate=0.01,
            max_event_rate=0.80,
            bootstrap_samples=100,
            rng_seed=20260430,
        ),
    )
    report = evaluate_noaa_coops_prereg(
        station_ids=stations,
        observed_paths=observed_paths,
        predictions_paths=predictions_paths,
        config=cfg,
    )
    assert report["schema"] == NOAA_COOPS_PREREG_REPORT_SCHEMA
    assert report["eligible_station_count"] == 3
    assert report["eligible_windows"] >= 2
    assert isinstance(report["failed_gates"], list)


def test_build_negative_result_summary_matches_schema(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report = {
        "schema": NOAA_COOPS_PREREG_REPORT_SCHEMA,
        "source": {"official_base_url": "https://example.test"},
        "inputs": [{"station": "8518750", "joined_rows": 10}],
        "result": {
            "source_audit_passed": True,
            "eligible_station_count": 1,
            "eligible_windows": 1,
            "overall_go_no_go": False,
            "result_status": "NEGATIVE_RESULT_UNDER_PROTOCOL",
        },
        "failed_gates": ["event rate below minimum in one window"],
        "external_payload_manifest_sha256": "abc",
        "acceptance": {},
        "config": {"protocol_version": "1.0.139"},
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    summary = build_negative_result_summary(report, report_path=report_path)
    assert summary["schema"] == NOAA_COOPS_NEGATIVE_SUMMARY_SCHEMA
    assert summary["failed_gates"] == ["event rate below minimum in one window"]


def test_noaa_coops_prereg_cli_writes_report_and_summary(tmp_path: Path) -> None:
    module = _load_cli_module()
    observed, predictions = _write_station_pair(tmp_path, "8518750", hours=5000, phase=0.0)
    report_path = tmp_path / "report.json"
    summary_path = tmp_path / "summary.json"
    argv = [
        "claimbound_run_noaa_coops_prereg.py",
        "--station",
        "8518750",
        "--observed",
        str(observed),
        "--predictions",
        str(predictions),
        "--report",
        str(report_path),
        "--summary",
        str(summary_path),
    ]
    previous_argv = sys.argv
    try:
        sys.argv = argv
        assert module.main() == 0
    finally:
        sys.argv = previous_argv
    assert report_path.is_file()
    assert summary_path.is_file()
