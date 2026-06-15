# SPDX-License-Identifier: Apache-2.0

"""NOAA CO-OPS D-131 frozen pre-registration evaluator.

Evaluates operator-supplied local NOAA CO-OPS JSON files under protocol 1.0.139.
Performs no network I/O and does not change gates.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from claimbound_evidence.baseline_groups import (
    Doc11AcceptanceConfig,
    WindowObservation,
    evaluate_group_vs_baseline_pool,
)
from claimbound_evidence.noaa_coops_fetch import NOAA_COOPS_D131_STATIONS
from claimbound_evidence.noaa_coops_parser import join_observed_predictions, sha256_of_file

NOAA_COOPS_PREREG_REPORT_SCHEMA = "noaa_coops_prereg_report_v1"
NOAA_COOPS_NEGATIVE_SUMMARY_SCHEMA = "claimbound_negative_result_summary_v1"
NOAA_COOPS_CANDIDATE_NAME = "noaa_coops_d131_abs_prediction_residual"
NOAA_COOPS_PROTOCOL_VERSION = "1.0.139"
HOURS_PER_YEAR = 365 * 24
# Shortest committed D-131 station row count (9414290) from the baseline summary.
NOAA_COOPS_MIN_JOINED_ROWS = 56424


@dataclass(frozen=True)
class NoaaCoopsPreregConfig:
    train_hours: int = 3 * HOURS_PER_YEAR
    test_hours: int = HOURS_PER_YEAR
    step_hours: int = HOURS_PER_YEAR
    event_quantile: float = 0.90
    minimum_test_event_count: int = 15
    min_joined_rows: int = int(0.95 * NOAA_COOPS_MIN_JOINED_ROWS)
    acceptance: Doc11AcceptanceConfig = field(
        default_factory=lambda: Doc11AcceptanceConfig(
            top_rate=0.10,
            min_windows=3,
            min_positive_rate=0.65,
            min_event_rate=0.03,
            max_event_rate=0.40,
            rng_seed=20260430,
        )
    )


def _sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hour_of_year_index(timestamp: datetime) -> int:
    return (timestamp.timetuple().tm_yday - 1) * 24 + timestamp.hour


def _seasonal_residual_scores(
    residual: NDArray[np.float64],
    timestamps: list[datetime],
    *,
    train_idx: NDArray[np.int64],
    test_idx: NDArray[np.int64],
) -> NDArray[np.float64]:
    by_hour: dict[int, list[float]] = {}
    for idx in train_idx.tolist():
        by_hour.setdefault(_hour_of_year_index(timestamps[idx]), []).append(float(residual[idx]))
    global_mean = float(np.mean(residual[train_idx]))
    scores = np.zeros(len(test_idx), dtype=np.float64)
    for pos, idx in enumerate(test_idx.tolist()):
        bucket = by_hour.get(_hour_of_year_index(timestamps[idx]), [])
        if len(bucket) >= 2:
            expected = float(np.mean(bucket))
        else:
            expected = global_mean
        scores[pos] = abs(float(residual[idx]) - expected)
    return scores


def _persistence_residual_scores(
    residual: NDArray[np.float64],
    test_idx: NDArray[np.int64],
) -> NDArray[np.float64]:
    shifted = np.roll(residual, 1)
    shifted[0] = residual[0]
    return np.abs(shifted[test_idx])


def _walk_forward_splits(n: int, cfg: NoaaCoopsPreregConfig) -> list[tuple[NDArray[np.int64], NDArray[np.int64]]]:
    splits: list[tuple[NDArray[np.int64], NDArray[np.int64]]] = []
    start = 0
    while start + cfg.train_hours + cfg.test_hours <= n:
        train = np.arange(start, start + cfg.train_hours, dtype=np.int64)
        test = np.arange(start + cfg.train_hours, start + cfg.train_hours + cfg.test_hours, dtype=np.int64)
        splits.append((train, test))
        start += cfg.step_hours
    return splits


def derive_failed_gates(acceptance: dict[str, object], *, cfg: NoaaCoopsPreregConfig) -> list[str]:
    failed: list[str] = []
    baseline_acceptance = acceptance.get("baseline_acceptance", {})
    if isinstance(baseline_acceptance, dict):
        seasonal = baseline_acceptance.get("seasonal_hour_of_year_residual", {})
        if isinstance(seasonal, dict) and not seasonal.get("meets_paired_gate", False):
            failed.append("seasonal hour-of-year residual control was not beaten")

    for record in acceptance.get("windows", []):
        if not isinstance(record, dict) or record.get("event_rate_in_range") is not False:
            continue
        rate = record.get("event_rate")
        if not isinstance(rate, (int, float)):
            continue
        if rate < cfg.acceptance.min_event_rate and "event rate below minimum in one window" not in failed:
            failed.append("event rate below minimum in one window")
        if rate > cfg.acceptance.max_event_rate and "event rate above maximum in one window" not in failed:
            failed.append("event rate above maximum in one window")
    return failed


def build_negative_result_summary(
    report: dict[str, object],
    *,
    report_path: Path,
) -> dict[str, object]:
    inputs = report.get("inputs", [])
    result = report.get("result", {})
    acceptance = report.get("acceptance", {})
    if not isinstance(inputs, list) or not isinstance(result, dict):
        raise ValueError("report missing inputs or result")
    if not isinstance(acceptance, dict):
        acceptance = {}

    cfg = report.get("config")
    protocol_version = NOAA_COOPS_PROTOCOL_VERSION
    if isinstance(cfg, dict):
        protocol_version = str(cfg.get("protocol_version", protocol_version))

    return {
        "schema": NOAA_COOPS_NEGATIVE_SUMMARY_SCHEMA,
        "domain": "NOAA_COOPS_D131",
        "protocol_version": protocol_version,
        "source": report.get("source", {}),
        "inputs": inputs,
        "report_sha256": sha256_of_file(report_path),
        "external_payload_manifest_sha256": report.get("external_payload_manifest_sha256"),
        "result": result,
        "failed_gates": report.get("failed_gates", []),
        "claim_boundary": {
            "allowed": "executed under a frozen protocol and recorded as NEGATIVE_RESULT_UNDER_PROTOCOL",
            "forbidden": [
                "accepted by protocol",
                "coastal-warning performance proven",
                "universal forecasting edge",
                "deployment readiness",
                "all statistical methods beaten",
            ],
        },
    }


def evaluate_noaa_coops_prereg(
    *,
    station_ids: list[str],
    observed_paths: list[Path],
    predictions_paths: list[Path],
    config: NoaaCoopsPreregConfig | None = None,
    pre_registration_doc_path: Path | None = None,
    external_payload_manifest_sha256: str | None = None,
) -> dict[str, object]:
    if not (len(station_ids) == len(observed_paths) == len(predictions_paths)):
        raise ValueError("station_ids, observed_paths and predictions_paths counts must match")

    cfg = config or NoaaCoopsPreregConfig()
    observations: list[WindowObservation] = []
    station_reports: list[dict[str, object]] = []
    input_summaries: list[dict[str, object]] = []
    source_audit_passed = True
    window_id = 0

    for station_id, observed_path, predictions_path in zip(
        station_ids, observed_paths, predictions_paths, strict=True
    ):
        timestamps, _observed, _predicted, residual, join_summary = join_observed_predictions(
            Path(observed_path),
            Path(predictions_path),
        )
        coverage_ok = int(join_summary["joined_rows"]) >= cfg.min_joined_rows
        source_audit_passed = source_audit_passed and coverage_ok
        station_windows: list[dict[str, object]] = []

        for train_idx, test_idx in _walk_forward_splits(len(residual), cfg):
            threshold = float(np.quantile(np.abs(residual[train_idx]), cfg.event_quantile))
            events = np.abs(residual[test_idx]) >= threshold
            event_count = int(np.sum(events))
            event_rate = float(np.mean(events)) if len(events) else None
            eligible = event_count >= cfg.minimum_test_event_count
            station_windows.append(
                {
                    "window_id": window_id,
                    "rows": int(len(test_idx)),
                    "events": event_count,
                    "event_rate": event_rate,
                    "eligible": bool(eligible),
                }
            )
            if eligible:
                observations.append(
                    WindowObservation(
                        candidate_scores=np.abs(residual[test_idx]),
                        baseline_scores={
                            "persistence_residual": _persistence_residual_scores(residual, test_idx),
                            "seasonal_hour_of_year_residual": _seasonal_residual_scores(
                                residual,
                                timestamps,
                                train_idx=train_idx,
                                test_idx=test_idx,
                            ),
                        },
                        events=events,
                        window_id=window_id,
                    )
                )
            window_id += 1

        input_summaries.append(
            {
                "station": station_id,
                "observed_sha256": join_summary["observed_sha256"],
                "predictions_sha256": join_summary["predictions_sha256"],
                "joined_rows": join_summary["joined_rows"],
            }
        )
        station_reports.append(
            {
                "station_id": station_id,
                "coverage_ok": coverage_ok,
                "join": join_summary,
                "windows": station_windows,
            }
        )

    acceptance = evaluate_group_vs_baseline_pool(observations, config=cfg.acceptance)
    eligible_station_count = sum(1 for station in station_reports if station["coverage_ok"])
    eligible_windows = len(observations)
    failed_gates = derive_failed_gates(acceptance, cfg=cfg)

    pre_reg_hash: str | None = None
    if pre_registration_doc_path is not None and pre_registration_doc_path.is_file():
        pre_reg_hash = _sha256_of_text(pre_registration_doc_path.read_text(encoding="utf-8"))

    source_audit_passed = source_audit_passed and eligible_station_count >= 3
    gate_passed = bool(acceptance.get("overall_go_no_go", False))
    overall = source_audit_passed and eligible_windows >= cfg.acceptance.min_windows and gate_passed
    if not source_audit_passed:
        result_status = "BLOCKED_SOURCE"
    elif overall:
        result_status = "PASSED_UNDER_PROTOCOL"
    else:
        result_status = "NEGATIVE_RESULT_UNDER_PROTOCOL"

    return {
        "schema": NOAA_COOPS_PREREG_REPORT_SCHEMA,
        "candidate": NOAA_COOPS_CANDIDATE_NAME,
        "config": {
            "protocol_version": NOAA_COOPS_PROTOCOL_VERSION,
            "train_hours": cfg.train_hours,
            "test_hours": cfg.test_hours,
            "step_hours": cfg.step_hours,
            "event_quantile": cfg.event_quantile,
            "minimum_test_event_count": cfg.minimum_test_event_count,
            "acceptance": acceptance.get("config", {}),
        },
        "pre_registration": {
            "doc": "NOAA_COOPS_D131_PREREG_CHARTER.md",
            "doc_sha256": pre_reg_hash,
        },
        "source": {
            "official_base_url": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
            "observed_product": "hourly_height",
            "prediction_product": "predictions",
            "datum": "MLLW",
            "time_zone": "gmt",
            "units": "metric",
            "format": "json",
            "period": "2018-01-01..2024-12-31",
            "stations": list(NOAA_COOPS_D131_STATIONS),
            "raw_payload_committed": False,
        },
        "source_audit_passed": bool(source_audit_passed),
        "eligible_station_count": int(eligible_station_count),
        "eligible_windows": int(eligible_windows),
        "stations": station_reports,
        "acceptance": acceptance,
        "failed_gates": failed_gates,
        "inputs": input_summaries,
        "external_payload_manifest_sha256": external_payload_manifest_sha256,
        "overall_go_no_go": bool(overall),
        "result": {
            "source_audit_passed": bool(source_audit_passed),
            "eligible_station_count": int(eligible_station_count),
            "eligible_windows": int(eligible_windows),
            "overall_go_no_go": bool(overall),
            "result_status": result_status,
        },
        "result_status": result_status,
        "allowed_narrow_claim": (
            "passed the pre-registered NOAA CO-OPS D-131 gate under protocol 1.0.139"
            if overall
            else None
        ),
        "forbidden_claims": [
            "coastal-warning deployment readiness",
            "universal forecasting edge",
            "broad model superiority",
            "all statistical methods beaten",
        ],
        "honest_boundary": (
            "This report evaluates local NOAA CO-OPS JSON payloads under the frozen "
            "D-131 protocol. A positive claim requires overall_go_no_go=true; "
            "otherwise the result is negative or source-blocked evidence."
        ),
    }


__all__ = [
    "NOAA_COOPS_CANDIDATE_NAME",
    "NOAA_COOPS_NEGATIVE_SUMMARY_SCHEMA",
    "NOAA_COOPS_PREREG_REPORT_SCHEMA",
    "NOAA_COOPS_PROTOCOL_VERSION",
    "NoaaCoopsPreregConfig",
    "build_negative_result_summary",
    "derive_failed_gates",
    "evaluate_noaa_coops_prereg",
]
