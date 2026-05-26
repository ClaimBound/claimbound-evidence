# SPDX-License-Identifier: Apache-2.0

"""NASA POWER D-103 offline adapter/materializer.

The adapter implements only plumbing for the frozen D-103 pre-registration
charter. It can build deterministic mock daily solar-resource series for tests
or convert operator-supplied local NASA POWER JSON files into a generic OHLCV
CSV. It does not fetch network payloads and does not run the empirical gate.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from claimbound_evidence.nasa_power_parser import (
    parse_nasa_power_daily_json,
)


NASA_POWER_DATASET_ID_PREFIX = "nasa_power"
NASA_POWER_MANIFEST_SCHEMA = "nasa_power_manifest_v1"
NASA_POWER_PARAMETERS: tuple[str, ...] = (
    "ALLSKY_SFC_SW_DWN",
    "T2M",
    "WS10M",
    "PRECTOTCORR",
)
NASA_POWER_CSV_COLUMNS: tuple[str, ...] = (
    "time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


@dataclass(frozen=True)
class NasaPowerPoint:
    point_id: str
    name: str
    latitude: float
    longitude: float
    community: str = "RE"
    time_standard: str = "UTC"


NASA_POWER_POINTS: dict[str, NasaPowerPoint] = {
    "POWER_A": NasaPowerPoint("POWER_A", "Kyiv", 50.4501, 30.5234),
    "POWER_B": NasaPowerPoint("POWER_B", "Lviv", 49.8397, 24.0297),
    "POWER_C": NasaPowerPoint("POWER_C", "Odesa", 46.4825, 30.7233),
}


@dataclass(frozen=True)
class NasaPowerMockConfig:
    point_id: str
    start: date
    end: date
    seed: int | None = None
    solar_noise_std: float = 0.35

    def __post_init__(self) -> None:
        normalize_point_id(self.point_id)
        if self.start >= self.end:
            raise ValueError("start must be strictly less than end")
        if self.solar_noise_std < 0.0 or self.solar_noise_std > 20.0:
            raise ValueError("solar_noise_std must be in [0,20]")


def normalize_point_id(point_id: str) -> str:
    pid = str(point_id).strip().upper()
    if pid not in NASA_POWER_POINTS:
        known = ", ".join(sorted(NASA_POWER_POINTS))
        raise ValueError(f"unknown NASA POWER point {point_id!r}; known: {known}")
    return pid


def build_nasa_power_dataset_id(point_id: str, *, source_mode: str) -> str:
    pid = normalize_point_id(point_id)
    if source_mode == "mock":
        return f"{NASA_POWER_DATASET_ID_PREFIX}_{pid.lower()}_mock"
    if source_mode == "nasa_power_json_file":
        return f"{NASA_POWER_DATASET_ID_PREFIX}_{pid.lower()}"
    raise ValueError(f"unsupported source_mode {source_mode!r}")


def _seed_from_config(config: NasaPowerMockConfig) -> int:
    if config.seed is not None:
        return int(config.seed) & 0xFFFFFFFF
    material = f"{config.point_id}|{config.start.isoformat()}|{config.end.isoformat()}"
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:4], "big")


def _date_range(start: date, end: date) -> list[date]:
    days = int((end - start).days)
    if days < 1:
        raise ValueError("configured interval must contain at least one day")
    return [start + timedelta(days=i) for i in range(days)]


def trailing_mean(values: NDArray[np.float64], *, window: int) -> NDArray[np.float64]:
    if window < 1:
        raise ValueError("window must be >= 1")
    arr = np.asarray(values, dtype=np.float64)
    out = np.empty_like(arr)
    for idx in range(len(arr)):
        start = max(0, idx - window + 1)
        out[idx] = float(np.mean(arr[start : idx + 1]))
    return out


def generate_nasa_power_mock_daily_series(
    config: NasaPowerMockConfig,
) -> tuple[list[date], dict[str, NDArray[np.float64]]]:
    """Return deterministic daily parameter series for offline tests only."""

    rng = np.random.default_rng(_seed_from_config(config))
    days = _date_range(config.start, config.end)
    n = len(days)
    solar = np.empty(n, dtype=np.float64)
    temp = np.empty(n, dtype=np.float64)
    wind = np.empty(n, dtype=np.float64)
    precip = np.empty(n, dtype=np.float64)
    for idx, day in enumerate(days):
        seasonal = np.sin(2 * np.pi * (day.timetuple().tm_yday - 80) / 365.25)
        solar[idx] = max(0.0, 3.5 + 2.2 * seasonal)
        temp[idx] = 9.0 + 14.0 * seasonal
        wind[idx] = 4.0 + 0.8 * np.cos(2 * np.pi * idx / 9.0)
        precip[idx] = max(0.0, 1.2 + 1.0 * np.sin(2 * np.pi * idx / 17.0))
    solar += rng.normal(0.0, config.solar_noise_std, n)
    temp += rng.normal(0.0, 1.5, n)
    wind += rng.normal(0.0, 0.25, n)
    precip += rng.normal(0.0, 0.5, n)
    return days, {
        "ALLSKY_SFC_SW_DWN": np.maximum(solar, 0.0),
        "T2M": temp,
        "WS10M": np.maximum(wind, 0.0),
        "PRECTOTCORR": np.maximum(precip, 0.0),
    }


def parse_nasa_power_json_file(
    json_path: str | Path,
) -> tuple[list[date], dict[str, NDArray[np.float64]], dict[str, object]]:
    days, values, summary = parse_nasa_power_daily_json(
        json_path,
        parameters=NASA_POWER_PARAMETERS,
    )
    out_summary = {
        "parameters": list(summary.parameters),
        "rows": summary.rows,
        "skipped": summary.skipped,
        "first_date": summary.first_date.isoformat() if summary.first_date else None,
        "last_date": summary.last_date.isoformat() if summary.last_date else None,
    }
    return days, values, out_summary


def solar_7d_mean_from_values(values: dict[str, NDArray[np.float64]]) -> NDArray[np.float64]:
    if "ALLSKY_SFC_SW_DWN" not in values:
        raise ValueError("missing ALLSKY_SFC_SW_DWN values")
    return trailing_mean(values["ALLSKY_SFC_SW_DWN"], window=7)


def _iso_day(day: date) -> str:
    return f"{day.isoformat()}T00:00:00+00:00"


def write_nasa_power_solar_ohlcv_csv(
    days: list[date],
    solar_7d_mean: NDArray[np.float64],
    path: str | Path,
) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if len(days) != int(solar_7d_mean.shape[0]):
        raise ValueError("days length must match solar_7d_mean length")
    if len(days) == 0:
        raise ValueError("cannot write an empty daily series")
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(list(NASA_POWER_CSV_COLUMNS))
        for day, value in zip(days, solar_7d_mean.tolist(), strict=True):
            cell = f"{float(value):.6f}"
            writer.writerow([_iso_day(day), cell, cell, cell, cell, "1"])
    return out_path


def write_nasa_power_manifest(
    csv_path: str | Path,
    *,
    dataset_id: str,
    point_id: str,
    source_mode: str,
    start_date: date,
    end_date: date,
    rows: int,
    repo_semver: str | None,
    git_commit_short: str | None,
    manifest_path: str | Path | None = None,
) -> Path:
    csv_path_obj = Path(csv_path)
    if not csv_path_obj.is_file():
        raise FileNotFoundError(f"csv not found: {csv_path_obj}")
    pid = normalize_point_id(point_id)
    if source_mode not in {"mock", "nasa_power_json_file"}:
        raise ValueError(f"unsupported source_mode {source_mode!r}")
    point = NASA_POWER_POINTS[pid]
    manifest: dict[str, object] = {
        "schema": NASA_POWER_MANIFEST_SCHEMA,
        "dataset_id": dataset_id,
        "point_id": pid,
        "point_name": point.name,
        "point_location_redacted": True,
        "community": point.community,
        "time_standard": point.time_standard,
        "source_mode": source_mode,
        "parameters": list(NASA_POWER_PARAMETERS),
        "derived_series": "solar_7d_mean",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rows": int(rows),
        "generated_csv_committed": False,
        "repo_semver": repo_semver,
        "git_commit_short": git_commit_short,
        "raw_payload_committed": False,
        "honest_boundary": (
            "mock mode is synthetic plumbing only; nasa_power_json_file mode only "
            "materializes operator-supplied local official-source payloads and does "
            "not establish a positive empirical claim"
        ),
    }
    out_path = (
        Path(manifest_path)
        if manifest_path is not None
        else csv_path_obj.with_suffix(csv_path_obj.suffix + ".manifest.json")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return out_path


__all__ = [
    "NASA_POWER_MANIFEST_SCHEMA",
    "NASA_POWER_PARAMETERS",
    "NASA_POWER_POINTS",
    "NasaPowerMockConfig",
    "NasaPowerPoint",
    "build_nasa_power_dataset_id",
    "generate_nasa_power_mock_daily_series",
    "normalize_point_id",
    "parse_nasa_power_json_file",
    "solar_7d_mean_from_values",
    "trailing_mean",
    "write_nasa_power_manifest",
    "write_nasa_power_solar_ohlcv_csv",
]
