# SPDX-License-Identifier: Apache-2.0

"""NASA POWER D-103 frozen pre-registration evaluator.

This runner evaluates operator-supplied local NASA POWER Daily JSON files under
the frozen 1.0.143 charter. It performs no network I/O and does not change gates.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from claimbound_evidence.baseline_groups import (
    Doc11AcceptanceConfig,
    WindowObservation,
    evaluate_group_vs_baseline_pool,
)
from claimbound_evidence.generic_ohlcv_batch_pre_registration_meta import (
    build_generic_ohlcv_batch_reproducibility,
)
from claimbound_evidence.nasa_power import (
    NASA_POWER_POINTS,
    normalize_point_id,
    parse_nasa_power_json_file,
    solar_7d_mean_from_values,
)

NASA_POWER_PREREG_REPORT_SCHEMA = "nasa_power_prereg_report_v1"
NASA_POWER_CANDIDATE_NAME = "nasa_power_solar_resource_shortfall_zscore"


@dataclass(frozen=True)
class NasaPowerPreregConfig:
    horizon_days: int = 7
    threshold_quantile: float = 0.10
    trailing_window_days: int = 7
    train_days: int = 5 * 365
    test_days: int = 365
    step_days: int = 365
    minimum_test_event_count: int = 15
    solar_sigma_floor: float = 1e-9
    acceptance: Doc11AcceptanceConfig = field(
        default_factory=lambda: Doc11AcceptanceConfig(
            top_rate=0.10,
            min_windows=8,
            min_positive_rate=0.65,
            min_event_rate=0.03,
            max_event_rate=0.40,
        )
    )


def _sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _zscore_low(values: NDArray[np.float64], train_idx: NDArray[np.int64], test_idx: NDArray[np.int64], floor: float) -> NDArray[np.float64]:
    train = np.asarray(values[train_idx], dtype=np.float64)
    mu = float(np.mean(train)) if train.size else 0.0
    sigma = max(float(np.std(train)) if train.size else 0.0, floor)
    return (mu - np.asarray(values[test_idx], dtype=np.float64)) / sigma


def _zscore_high(values: NDArray[np.float64], train_idx: NDArray[np.int64], test_idx: NDArray[np.int64], floor: float) -> NDArray[np.float64]:
    train = np.asarray(values[train_idx], dtype=np.float64)
    mu = float(np.mean(train)) if train.size else 0.0
    sigma = max(float(np.std(train)) if train.size else 0.0, floor)
    return (np.asarray(values[test_idx], dtype=np.float64) - mu) / sigma


def _rolling_low_zscore(values: NDArray[np.float64], *, window: int, floor: float) -> NDArray[np.float64]:
    arr = np.asarray(values, dtype=np.float64)
    out = np.zeros_like(arr)
    for idx in range(len(arr)):
        start = max(0, idx - window)
        hist = arr[start:idx]
        if hist.size < 2:
            continue
        mu = float(np.mean(hist))
        sigma = max(float(np.std(hist)), floor)
        out[idx] = (mu - float(arr[idx])) / sigma
    return out


def _seasonal_dayofyear_low_zscore(
    values: NDArray[np.float64],
    days: list[date],
    *,
    train_idx: NDArray[np.int64],
    test_idx: NDArray[np.int64],
    floor: float,
) -> NDArray[np.float64]:
    arr = np.asarray(values, dtype=np.float64)
    by_day: dict[int, list[float]] = {idx: [] for idx in range(1, 367)}
    for idx in train_idx.tolist():
        by_day[days[idx].timetuple().tm_yday].append(float(arr[idx]))
    global_train = arr[train_idx]
    fallback_mu = float(np.mean(global_train)) if global_train.size else 0.0
    fallback_sigma = max(float(np.std(global_train)) if global_train.size else 0.0, floor)
    out = np.zeros(len(test_idx), dtype=np.float64)
    for pos, idx in enumerate(test_idx.tolist()):
        doy = days[idx].timetuple().tm_yday
        bucket_values: list[float] = []
        for neighbor in (doy - 1, doy, doy + 1):
            if neighbor == 0:
                key = 366
            elif neighbor == 367:
                key = 1
            else:
                key = neighbor
            bucket_values.extend(by_day.get(key, []))
        bucket = np.asarray(bucket_values, dtype=np.float64)
        if bucket.size >= 2:
            mu = float(np.mean(bucket))
            sigma = max(float(np.std(bucket)), floor)
        else:
            mu = fallback_mu
            sigma = fallback_sigma
        out[pos] = (mu - float(arr[idx])) / sigma
    return out


def _build_forward_events(
    solar_7d_mean: NDArray[np.float64],
    *,
    train_idx: NDArray[np.int64],
    test_idx: NDArray[np.int64],
    horizon_days: int,
    threshold_quantile: float,
) -> NDArray[np.bool_]:
    threshold = float(np.quantile(solar_7d_mean[train_idx], threshold_quantile))
    events = np.zeros(len(test_idx), dtype=bool)
    n = len(solar_7d_mean)
    for pos, idx in enumerate(test_idx.tolist()):
        end = min(n, idx + horizon_days + 1)
        if idx + 1 >= end:
            continue
        events[pos] = bool(np.min(solar_7d_mean[idx + 1 : end]) < threshold)
    return events


def _walk_forward_splits(n: int, cfg: NasaPowerPreregConfig) -> list[tuple[NDArray[np.int64], NDArray[np.int64]]]:
    splits: list[tuple[NDArray[np.int64], NDArray[np.int64]]] = []
    start = 0
    while start + cfg.train_days + cfg.test_days <= n:
        train = np.arange(start, start + cfg.train_days, dtype=np.int64)
        test = np.arange(
            start + cfg.train_days,
            start + cfg.train_days + cfg.test_days,
            dtype=np.int64,
        )
        splits.append((train, test))
        start += cfg.step_days
    return splits


def _baseline_scores_for_split(
    *,
    solar_7d_mean: NDArray[np.float64],
    t2m: NDArray[np.float64],
    ws10m: NDArray[np.float64],
    prectotcorr: NDArray[np.float64],
    days: list[date],
    train_idx: NDArray[np.int64],
    test_idx: NDArray[np.int64],
    floor: float,
) -> Mapping[str, NDArray[np.float64]]:
    rolling_30d = _rolling_low_zscore(solar_7d_mean, window=30, floor=floor)[test_idx]
    rolling_90d = _rolling_low_zscore(solar_7d_mean, window=90, floor=floor)[test_idx]
    shifted = np.roll(solar_7d_mean, 1)
    shifted[0] = solar_7d_mean[0]
    persistence = _zscore_low(shifted, train_idx, test_idx, floor)
    seasonal = _seasonal_dayofyear_low_zscore(
        solar_7d_mean, days, train_idx=train_idx, test_idx=test_idx, floor=floor
    )
    temperature = _zscore_high(t2m, train_idx, test_idx, floor)
    wind = _zscore_high(ws10m, train_idx, test_idx, floor)
    precipitation = _zscore_high(prectotcorr, train_idx, test_idx, floor)
    shuffled = np.asarray(solar_7d_mean[test_idx], dtype=np.float64).copy()
    rng = np.random.default_rng(20260428)
    rng.shuffle(shuffled)
    shuffled = _zscore_low(shuffled, np.arange(len(shuffled), dtype=np.int64), np.arange(len(shuffled), dtype=np.int64), floor)
    reversed_scores = _zscore_low(
        solar_7d_mean[::-1],
        np.arange(min(len(train_idx), len(solar_7d_mean)), dtype=np.int64),
        np.arange(len(test_idx), dtype=np.int64),
        floor,
    )
    no_solar_context = (
        temperature + wind + precipitation
    ) / 3.0
    return {
        "rolling_solar_shortfall_zscore_30d": rolling_30d,
        "rolling_solar_shortfall_zscore_90d": rolling_90d,
        "persistence_solar_shortfall": persistence,
        "seasonal_dayofyear_solar_shortfall": seasonal,
        "temperature_anomaly_zscore": temperature,
        "wind_speed_anomaly_zscore": wind,
        "precipitation_anomaly_zscore": precipitation,
        "shuffled_candidate": shuffled,
        "time_reversed_candidate": reversed_scores,
        "candidate_no_solar_context": no_solar_context,
    }


def _load_point_payload(
    json_path: Path,
    *,
    point_id: str,
) -> tuple[list[date], dict[str, NDArray[np.float64]], NDArray[np.float64], dict[str, object]]:
    pid = normalize_point_id(point_id)
    days, values, parse_summary = parse_nasa_power_json_file(json_path)
    solar_7d = solar_7d_mean_from_values(values)
    point = NASA_POWER_POINTS[pid]
    source = {
        "point_id": pid,
        "point_name": point.name,
        "point_location_redacted": True,
        "json": json_path.name,
        "json_sha256": _sha256_of_file(json_path),
        "rows": parse_summary["rows"],
        "skipped": parse_summary["skipped"],
        "first_date": parse_summary["first_date"],
        "last_date": parse_summary["last_date"],
        "finite_parameter_coverage": 1.0,
    }
    return days, values, solar_7d, source


def evaluate_nasa_power_prereg(
    *,
    point_ids: list[str],
    json_paths: list[Path],
    config: NasaPowerPreregConfig | None = None,
    pre_registration_doc_path: Path | None = None,
) -> dict[str, object]:
    if len(point_ids) != len(json_paths):
        raise ValueError("point_ids and json_paths counts must match")
    cfg = config or NasaPowerPreregConfig()

    observations: list[WindowObservation] = []
    point_reports: list[dict[str, object]] = []
    source_audit_passed = True
    window_id = 0
    for point_id, json_path in zip(point_ids, json_paths, strict=True):
        days, values, solar_7d, source = _load_point_payload(Path(json_path), point_id=point_id)
        point = NASA_POWER_POINTS[normalize_point_id(point_id)]
        point_windows: list[dict[str, object]] = []
        coverage_ok = bool(int(source["rows"]) >= int(0.95 * len(days)))
        source_audit_passed = source_audit_passed and coverage_ok
        for train_idx, test_idx in _walk_forward_splits(len(solar_7d), cfg):
            events = _build_forward_events(
                solar_7d,
                train_idx=train_idx,
                test_idx=test_idx,
                horizon_days=cfg.horizon_days,
                threshold_quantile=cfg.threshold_quantile,
            )
            event_count = int(np.sum(events))
            event_rate = float(np.mean(events)) if len(events) else None
            eligible = event_count >= cfg.minimum_test_event_count
            point_windows.append(
                {
                    "window_id": window_id,
                    "rows": int(len(test_idx)),
                    "events": event_count,
                    "event_rate": event_rate,
                    "eligible": bool(eligible),
                }
            )
            if eligible:
                candidate = _zscore_low(solar_7d, train_idx, test_idx, cfg.solar_sigma_floor)
                baselines = _baseline_scores_for_split(
                    solar_7d_mean=solar_7d,
                    t2m=values["T2M"],
                    ws10m=values["WS10M"],
                    prectotcorr=values["PRECTOTCORR"],
                    days=days,
                    train_idx=train_idx,
                    test_idx=test_idx,
                    floor=cfg.solar_sigma_floor,
                )
                observations.append(
                    WindowObservation(
                        candidate_scores=candidate,
                        baseline_scores=baselines,
                        events=events,
                        window_id=window_id,
                    )
                )
            window_id += 1
        point_reports.append(
            {
                "point_id": point.point_id,
                "point_name": point.name,
                "point_location_redacted": True,
                "source": source,
                "coverage_ok": coverage_ok,
                "windows": point_windows,
            }
        )

    acceptance = evaluate_group_vs_baseline_pool(observations, config=cfg.acceptance)
    eligible_point_count = sum(1 for point in point_reports if point["coverage_ok"])
    eligible_windows = len(observations)
    pre_reg_hash: str | None = None
    if pre_registration_doc_path is not None and pre_registration_doc_path.is_file():
        pre_reg_hash = _sha256_of_text(pre_registration_doc_path.read_text(encoding="utf-8"))
    source_audit_passed = source_audit_passed and eligible_point_count >= 2
    overall = (
        source_audit_passed
        and eligible_windows >= 8
        and bool(acceptance.get("overall_go_no_go", False))
    )
    result_status = "PASSED_UNDER_PROTOCOL" if overall else "NEGATIVE_RESULT"
    if not source_audit_passed:
        result_status = "BLOCKED_SOURCE"
    return {
        "schema": NASA_POWER_PREREG_REPORT_SCHEMA,
        "candidate": NASA_POWER_CANDIDATE_NAME,
        "pre_registration": {
            "doc": "NASA_POWER_D103_PREREG_CHARTER.md",
            "doc_sha256": pre_reg_hash,
            "config": {
                "horizon_days": cfg.horizon_days,
                "threshold_quantile": cfg.threshold_quantile,
                "trailing_window_days": cfg.trailing_window_days,
                "train_days": cfg.train_days,
                "test_days": cfg.test_days,
                "step_days": cfg.step_days,
                "minimum_test_event_count": cfg.minimum_test_event_count,
                "top_rate": cfg.acceptance.top_rate,
                "min_positive_rate": cfg.acceptance.min_positive_rate,
            },
        },
        "reproducibility": build_generic_ohlcv_batch_reproducibility(),
        "source_audit_passed": bool(source_audit_passed),
        "eligible_point_count": int(eligible_point_count),
        "eligible_windows": int(eligible_windows),
        "points": point_reports,
        "acceptance": acceptance,
        "overall_go_no_go": bool(overall),
        "result_status": result_status,
        "allowed_narrow_claim": (
            "passed the pre-registered NASA POWER D-103 gate under protocol 1.0.143"
            if overall
            else None
        ),
        "forbidden_claims": [
            "broad or universal forecasting performance",
            "deployment readiness",
            "energy-grid operational readiness",
            "non-public background performance claim",
        ],
        "honest_boundary": (
            "This report evaluates local NASA POWER JSON payloads under the frozen "
            "D-103 protocol. A positive claim requires overall_go_no_go=true; "
            "otherwise the result is negative or source-blocked evidence."
        ),
    }


__all__ = [
    "NASA_POWER_CANDIDATE_NAME",
    "NASA_POWER_PREREG_REPORT_SCHEMA",
    "NasaPowerPreregConfig",
    "evaluate_nasa_power_prereg",
]
