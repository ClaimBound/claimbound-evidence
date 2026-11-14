# SPDX-License-Identifier: Apache-2.0

"""Offline NASA POWER Daily JSON parser for the D-103 pre-registration path.

This module parses JSON files that the operator has already saved outside the
repository. It performs no network I/O and does not validate any empirical
claim. The supported shape matches the NASA POWER daily point JSON convention:
``properties.parameter`` contains one object per parameter, keyed by YYYYMMDD.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class NasaPowerParseSummary:
    """Summary of a local NASA POWER Daily JSON parse."""

    parameters: tuple[str, ...]
    rows: int
    skipped: int
    first_date: date | None
    last_date: date | None


def _parse_date_key(raw: object) -> date | None:
    text = str(raw).strip() if raw is not None else ""
    if not text:
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_value(raw: object) -> float | None:
    text = str(raw).strip() if raw is not None else ""
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if not np.isfinite(value):
        return None
    if value <= -900.0:
        return None
    return value


def _parameter_payload(payload: dict[str, object]) -> dict[str, object]:
    props = payload.get("properties")
    if not isinstance(props, dict):
        raise ValueError("NASA POWER JSON must contain object key 'properties'")
    params = props.get("parameter")
    if not isinstance(params, dict):
        raise ValueError("NASA POWER JSON must contain object key 'properties.parameter'")
    return params


def parse_nasa_power_daily_json(
    path: str | Path,
    *,
    parameters: tuple[str, ...],
) -> tuple[list[date], dict[str, NDArray[np.float64]], NasaPowerParseSummary]:
    """Parse selected parameters from a local NASA POWER Daily JSON file."""

    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"NASA POWER JSON not found: {file_path}")
    if not parameters:
        raise ValueError("parameters must not be empty")
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"NASA POWER JSON root must be an object: {file_path}")
    params = _parameter_payload(payload)

    missing = [param for param in parameters if param not in params]
    if missing:
        raise ValueError(f"NASA POWER JSON missing parameters: {', '.join(missing)}")

    by_date: dict[date, dict[str, float]] = {}
    skipped = 0
    for param in parameters:
        raw_series = params[param]
        if not isinstance(raw_series, dict):
            raise ValueError(f"NASA POWER parameter {param!r} must be an object")
        for raw_key, raw_value in raw_series.items():
            day = _parse_date_key(raw_key)
            value = _parse_value(raw_value)
            if day is None or value is None:
                skipped += 1
                continue
            by_date.setdefault(day, {})[param] = value

    rows: list[tuple[date, dict[str, float]]] = []
    for day, values in by_date.items():
        if all(param in values for param in parameters):
            rows.append((day, values))
        else:
            skipped += 1
    rows.sort(key=lambda row: row[0])
    if not rows:
        raise ValueError("NASA POWER JSON contained no complete usable daily rows")

    days = [row[0] for row in rows]
    values_by_param = {
        param: np.asarray([row[1][param] for row in rows], dtype=np.float64)
        for param in parameters
    }
    summary = NasaPowerParseSummary(
        parameters=tuple(parameters),
        rows=len(days),
        skipped=int(skipped),
        first_date=days[0],
        last_date=days[-1],
    )
    return days, values_by_param, summary


__all__ = [
    "NasaPowerParseSummary",
    "parse_nasa_power_daily_json",
]
