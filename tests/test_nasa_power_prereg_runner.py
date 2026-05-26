# SPDX-License-Identifier: Apache-2.0
"""Offline tests for NASA POWER D-103 prereg runner."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

from claimbound_evidence.baseline_groups import Doc11AcceptanceConfig
from claimbound_evidence.nasa_power_prereg_runner import (
    NASA_POWER_PREREG_REPORT_SCHEMA,
    NasaPowerPreregConfig,
    evaluate_nasa_power_prereg,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_power_fixture(path: Path, *, days: int, phase: float) -> None:
    start = date(2020, 1, 1)
    params = {
        "ALLSKY_SFC_SW_DWN": {},
        "T2M": {},
        "WS10M": {},
        "PRECTOTCORR": {},
    }
    for i in range(days):
        day = start + timedelta(days=i)
        key = day.strftime("%Y%m%d")
        seasonal = 1.0 + ((i + int(phase)) % 31) / 31.0
        if i % 41 in {0, 1, 2, 3}:
            seasonal *= 0.25
        params["ALLSKY_SFC_SW_DWN"][key] = round(seasonal, 6)
        params["T2M"][key] = round(8.0 + ((i + int(phase)) % 19) / 3.0, 6)
        params["WS10M"][key] = round(2.0 + (i % 7) / 10.0, 6)
        params["PRECTOTCORR"][key] = round((i % 5) / 10.0, 6)
    path.write_text(
        json.dumps({"type": "Feature", "properties": {"parameter": params}}),
        encoding="utf-8",
    )


def _load_cli_module():
    script_path = REPO_ROOT / "scripts" / "claimbound_run_nasa_power_prereg.py"
    import importlib.util as ilu

    spec = ilu.spec_from_file_location("pb_run_nasa_power_prereg_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nasa_power_prereg_runner_report_shape(tmp_path: Path) -> None:
    paths = [tmp_path / "a.json", tmp_path / "b.json"]
    _write_power_fixture(paths[0], days=120, phase=0.0)
    _write_power_fixture(paths[1], days=120, phase=5.0)
    cfg = NasaPowerPreregConfig(
        horizon_days=5,
        train_days=48,
        test_days=24,
        step_days=24,
        minimum_test_event_count=1,
        acceptance=Doc11AcceptanceConfig(
            top_rate=0.10,
            min_windows=2,
            min_positive_rate=0.65,
            min_event_rate=0.01,
            max_event_rate=0.80,
            bootstrap_samples=100,
        ),
    )
    report = evaluate_nasa_power_prereg(
        point_ids=["POWER_A", "POWER_B"],
        json_paths=paths,
        config=cfg,
    )

    assert report["schema"] == NASA_POWER_PREREG_REPORT_SCHEMA
    assert report["candidate"] == "nasa_power_solar_resource_shortfall_zscore"
    assert report["eligible_point_count"] == 2
    assert report["source_audit_passed"] is True
    assert report["result_status"] in {
        "PASSED_UNDER_PROTOCOL",
        "NEGATIVE_RESULT",
        "BLOCKED_SOURCE",
    }
    assert report["allowed_narrow_claim"] is None or "NASA POWER D-103" in str(
        report["allowed_narrow_claim"]
    )
    assert "rolling_solar_shortfall_zscore_30d" in report["acceptance"]["baseline_names"]
    assert "candidate_no_solar_context" in report["acceptance"]["baseline_names"]
    for point_report in report["points"]:
        assert point_report["point_location_redacted"] is True
        assert "latitude" not in point_report
        assert "longitude" not in point_report
        assert point_report["source"]["point_location_redacted"] is True
        assert "latitude" not in point_report["source"]
        assert "longitude" not in point_report["source"]


def test_nasa_power_prereg_cli_help(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_cli_module()
    monkeypatch.setattr(sys, "argv", ["pb_run_nasa_power_prereg.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        module.main()  # type: ignore[attr-defined]
    assert exc.value.code == 0
