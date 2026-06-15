# SPDX-License-Identifier: Apache-2.0
"""Tests for NOAA CO-OPS D-131 JSON parser."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claimbound_evidence.noaa_coops_parser import join_observed_predictions, parse_noaa_coops_series


def _write_hourly_payload(path: Path, *, product: str, values: list[float]) -> None:
    start = datetime(2020, 1, 1)
    rows = []
    for idx, value in enumerate(values):
        ts = start + timedelta(hours=idx)
        rows.append({"t": ts.strftime("%Y-%m-%d %H:%M"), "v": str(value)})
    payload = {"data": rows} if product == "hourly_height" else {"predictions": rows}
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_parse_noaa_coops_series_skips_empty_values(tmp_path: Path) -> None:
    path = tmp_path / "observed.json"
    _write_hourly_payload(path, product="hourly_height", values=[1.0, 2.0, 3.0])
    timestamps, values, summary = parse_noaa_coops_series(path)
    assert len(timestamps) == 3
    assert summary["finite_rows"] == 3


def test_join_observed_predictions_aligns_timestamps(tmp_path: Path) -> None:
    observed = tmp_path / "8518750_observed.json"
    predictions = tmp_path / "8518750_predictions.json"
    _write_hourly_payload(observed, product="hourly_height", values=[1.0, 2.0, 3.0, 4.0])
    _write_hourly_payload(predictions, product="predictions", values=[0.5, 1.5, 2.5, 9.0])
    timestamps, obs, pred, resid, summary = join_observed_predictions(observed, predictions)
    assert len(timestamps) == 4
    assert summary["joined_rows"] == 4
    assert list(resid) == pytest.approx([0.5, 0.5, 0.5, -5.0])
