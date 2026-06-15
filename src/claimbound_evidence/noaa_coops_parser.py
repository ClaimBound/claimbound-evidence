# SPDX-License-Identifier: Apache-2.0

"""Parse and join NOAA CO-OPS D-131 local JSON payloads."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from claimbound_evidence.noaa_coops_fetch import NOAA_COOPS_D131_STATIONS


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_noaa_coops_series(path: Path) -> tuple[list[datetime], NDArray[np.float64], dict[str, object]]:
    """Parse one NOAA CO-OPS hourly_height or predictions JSON file."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if "error" in payload:
        raise ValueError(str(payload["error"]))

    rows = payload.get("data")
    if rows is None:
        rows = payload.get("predictions")
    if not isinstance(rows, list):
        raise ValueError(f"{path.name}: expected data or predictions list")

    timestamps: list[datetime] = []
    values: list[float] = []
    skipped = 0
    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        raw_value = row.get("v")
        if raw_value in (None, "", " "):
            skipped += 1
            continue
        timestamps.append(datetime.strptime(str(row["t"]), "%Y-%m-%d %H:%M"))
        values.append(float(raw_value))

    if not timestamps:
        raise ValueError(f"{path.name}: no finite observations")

    return (
        timestamps,
        np.asarray(values, dtype=np.float64),
        {
            "json": path.name,
            "json_sha256": sha256_of_file(path),
            "rows": len(rows),
            "finite_rows": len(values),
            "skipped": skipped,
            "first_timestamp": timestamps[0].isoformat(sep=" "),
            "last_timestamp": timestamps[-1].isoformat(sep=" "),
        },
    )


def join_observed_predictions(
    observed_path: Path,
    predictions_path: Path,
) -> tuple[list[datetime], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], dict[str, object]]:
    """Join observed and prediction series on timestamp."""

    obs_ts, obs_values, obs_summary = parse_noaa_coops_series(observed_path)
    pred_ts, pred_values, pred_summary = parse_noaa_coops_series(predictions_path)

    obs_map = {ts: value for ts, value in zip(obs_ts, obs_values, strict=True)}
    pred_map = {ts: value for ts, value in zip(pred_ts, pred_values, strict=True)}
    shared = sorted(set(obs_map) & set(pred_map))
    if not shared:
        raise ValueError(
            f"no shared timestamps between {observed_path.name} and {predictions_path.name}"
        )

    observed = np.asarray([obs_map[ts] for ts in shared], dtype=np.float64)
    predicted = np.asarray([pred_map[ts] for ts in shared], dtype=np.float64)
    residual = observed - predicted
    return (
        shared,
        observed,
        predicted,
        residual,
        {
            "observed": obs_summary,
            "predictions": pred_summary,
            "joined_rows": len(shared),
            "observed_sha256": obs_summary["json_sha256"],
            "predictions_sha256": pred_summary["json_sha256"],
        },
    )


def default_station_paths(raw_dir: Path, station: str) -> tuple[Path, Path]:
    if station not in NOAA_COOPS_D131_STATIONS:
        raise ValueError(f"unknown D-131 station: {station!r}")
    return (
        raw_dir / f"{station}_observed.json",
        raw_dir / f"{station}_predictions.json",
    )


__all__ = [
    "default_station_paths",
    "join_observed_predictions",
    "parse_noaa_coops_series",
    "sha256_of_file",
]
