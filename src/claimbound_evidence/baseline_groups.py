# SPDX-License-Identifier: Apache-2.0

"""Baseline groups and doc-11 paired acceptance evaluator.

This module exposes the three baseline groups required by doc 11:

* ``stat_baselines_only``    — zscore_rolling, ewma_residual, stl_residual,
                                persistence_residual;
* ``ml_anomaly_baselines_only`` — knn_lof, isolation_tree;
* ``all_baselines``          — union of the two groups above.

It also provides :func:`evaluate_group_vs_baseline_pool`, a deterministic
paired acceptance evaluator which — for a given candidate group score and a
pool of baseline scores across ``>=3`` independent windows — computes:

* per-window precision-at-top-rate of each scorer;
* paired ``positive_rate`` of candidate over every baseline;
* bootstrap percentile CI of the mean candidate-minus-baseline delta;
* overall go/no-go vs the combined pool (must beat every baseline).

The acceptance gates match doc 53: ``positive_rate >= 0.70``,
``mean_delta > 0``, bootstrap CI excludes zero uplift, ``>= 3`` independent
windows, ``beats all baselines``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from claimbound_evidence.baselines import (
    DOC11_BASELINE_NAMES,
    BaselinePoolConfig,
    compute_baseline_scores,
    normalize_baseline_score,
)

STAT_BASELINE_NAMES: tuple[str, ...] = (
    "zscore_rolling",
    "ewma_residual",
    "stl_residual",
    "persistence_residual",
)

ML_ANOMALY_BASELINE_NAMES: tuple[str, ...] = (
    "knn_lof",
    "isolation_tree",
)

DOC11_BASELINE_GROUPS: dict[str, tuple[str, ...]] = {
    "stat_baselines_only": STAT_BASELINE_NAMES,
    "ml_anomaly_baselines_only": ML_ANOMALY_BASELINE_NAMES,
    "all_baselines": DOC11_BASELINE_NAMES,
}


@dataclass(frozen=True)
class Doc11AcceptanceConfig:
    """Acceptance-gate configuration (doc 53 defaults)."""

    top_rate: float = 0.2
    min_windows: int = 3
    min_positive_rate: float = 0.70
    min_event_rate: float = 0.03
    max_event_rate: float = 0.40
    bootstrap_samples: int = 2000
    bootstrap_ci: float = 0.95
    rng_seed: int = 4242


@dataclass(frozen=True)
class BaselinePoolScores:
    """Container for a precomputed baseline pool at a given rowset."""

    raw: dict[str, NDArray[np.float64]]
    config: BaselinePoolConfig = field(default_factory=BaselinePoolConfig)


def build_baseline_pool_scores(
    prices: NDArray[np.float64],
    *,
    config: BaselinePoolConfig | None = None,
) -> BaselinePoolScores:
    """Compute the full doc-11 baseline pool aligned with ``prices``."""

    cfg = config or BaselinePoolConfig()
    raw = compute_baseline_scores(prices, config=cfg)
    return BaselinePoolScores(raw=raw, config=cfg)


def normalized_baseline_scores_for_split(
    pool: BaselinePoolScores,
    *,
    train_idx: NDArray[np.int64],
    test_idx: NDArray[np.int64],
    group: str = "all_baselines",
) -> dict[str, NDArray[np.float64]]:
    """Train-only-normalized scores for a split, filtered by baseline group."""

    if group not in DOC11_BASELINE_GROUPS:
        raise KeyError(f"Unknown baseline group: {group!r}")
    names = DOC11_BASELINE_GROUPS[group]
    out: dict[str, NDArray[np.float64]] = {}
    for name in names:
        values = pool.raw[name]
        out[name] = normalize_baseline_score(values, train_idx, test_idx)
    return out


def _precision_at_top(
    scores: NDArray[np.float64],
    events: NDArray[np.bool_],
    top_rate: float,
) -> float | None:
    scores_arr = np.asarray(scores, dtype=np.float64)
    events_arr = np.asarray(events, dtype=bool)
    if len(scores_arr) == 0 or len(events_arr) == 0:
        return None
    count = max(1, int(np.ceil(len(scores_arr) * top_rate)))
    order = np.argsort(-scores_arr)
    selected = order[:count]
    return float(np.mean(events_arr[selected]))


def _bootstrap_mean_ci(
    values: Sequence[float],
    *,
    samples: int,
    ci: float,
    rng_seed: int,
) -> tuple[float | None, float | None, float | None]:
    arr = np.asarray(values, dtype=np.float64)
    if len(arr) == 0:
        return (None, None, None)
    if len(arr) == 1:
        return (float(arr[0]), float(arr[0]), float(arr[0]))
    rng = np.random.default_rng(rng_seed)
    boot = np.empty(samples, dtype=np.float64)
    n = len(arr)
    for s in range(samples):
        draw = rng.integers(0, n, size=n)
        boot[s] = float(np.mean(arr[draw]))
    alpha = (1.0 - ci) / 2.0
    low = float(np.quantile(boot, alpha))
    high = float(np.quantile(boot, 1.0 - alpha))
    return (float(np.mean(arr)), low, high)


@dataclass(frozen=True)
class WindowObservation:
    """Per-window inputs to the acceptance evaluator."""

    candidate_scores: NDArray[np.float64]
    baseline_scores: Mapping[str, NDArray[np.float64]]
    events: NDArray[np.bool_]
    window_id: int


def _per_window_precisions(
    obs: WindowObservation,
    *,
    top_rate: float,
) -> dict[str, float | None]:
    out: dict[str, float | None] = {"candidate": _precision_at_top(obs.candidate_scores, obs.events, top_rate)}
    for name, scores in obs.baseline_scores.items():
        out[name] = _precision_at_top(scores, obs.events, top_rate)
    return out


def _event_rate(events: NDArray[np.bool_]) -> float | None:
    events_arr = np.asarray(events, dtype=bool)
    return float(np.mean(events_arr)) if len(events_arr) else None


def _positive_rate(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return float(sum(1 for value in values if value > 0.0) / len(values))


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return float(np.mean(np.asarray(values, dtype=np.float64)))


def evaluate_group_vs_baseline_pool(
    observations: Sequence[WindowObservation],
    *,
    config: Doc11AcceptanceConfig | None = None,
) -> dict[str, object]:
    """Paired doc-11/doc-53 acceptance evaluator over ``>=min_windows`` windows.

    For each window computes precision-at-top of candidate and every baseline
    and per-baseline delta; aggregates across windows with bootstrap CIs and
    emits an overall go/no-go that is ``True`` only if **every** baseline is
    beaten by all gate criteria simultaneously.
    """

    cfg = config or Doc11AcceptanceConfig()
    window_records: list[dict[str, object]] = []
    baseline_names: tuple[str, ...] = ()
    for obs in observations:
        baseline_names = tuple(obs.baseline_scores.keys())
        per_precision = _per_window_precisions(obs, top_rate=cfg.top_rate)
        rate = _event_rate(obs.events)
        window_records.append(
            {
                "window_id": int(obs.window_id),
                "event_rate": rate,
                "evaluated": int(len(obs.events)),
                "events": int(np.sum(np.asarray(obs.events, dtype=bool))),
                "precision": per_precision,
                "event_rate_in_range": (
                    None
                    if rate is None
                    else bool(cfg.min_event_rate <= rate <= cfg.max_event_rate)
                ),
            }
        )

    baseline_acceptance: dict[str, dict[str, object]] = {}
    for name in baseline_names:
        deltas: list[float] = []
        for record in window_records:
            precision = record["precision"]
            assert isinstance(precision, dict)
            candidate = precision.get("candidate")
            baseline = precision.get(name)
            if candidate is None or baseline is None:
                continue
            deltas.append(float(candidate) - float(baseline))
        positive = _positive_rate(deltas)
        mean_delta = _mean(deltas)
        mean_boot, ci_low, ci_high = _bootstrap_mean_ci(
            deltas,
            samples=cfg.bootstrap_samples,
            ci=cfg.bootstrap_ci,
            rng_seed=cfg.rng_seed,
        )
        ci_excludes_zero = (
            ci_low is not None and ci_high is not None and ci_low > 0.0
        )
        meets = (
            len(deltas) >= cfg.min_windows
            and positive is not None
            and positive >= cfg.min_positive_rate
            and mean_delta is not None
            and mean_delta > 0.0
            and ci_excludes_zero
        )
        baseline_acceptance[name] = {
            "windows": len(deltas),
            "positive_rate": positive,
            "mean_delta": mean_delta,
            "bootstrap_mean": mean_boot,
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
            "bootstrap_ci_excludes_zero": bool(ci_excludes_zero),
            "meets_paired_gate": bool(meets),
        }

    event_rate_ok = all(
        record.get("event_rate_in_range") is True for record in window_records
    )
    overall_go = (
        len(window_records) >= cfg.min_windows
        and event_rate_ok
        and bool(baseline_acceptance)
        and all(payload.get("meets_paired_gate") for payload in baseline_acceptance.values())
    )
    return {
        "config": {
            "top_rate": cfg.top_rate,
            "min_windows": cfg.min_windows,
            "min_positive_rate": cfg.min_positive_rate,
            "min_event_rate": cfg.min_event_rate,
            "max_event_rate": cfg.max_event_rate,
            "bootstrap_samples": cfg.bootstrap_samples,
            "bootstrap_ci": cfg.bootstrap_ci,
            "rng_seed": cfg.rng_seed,
        },
        "baseline_names": list(baseline_names),
        "windows": window_records,
        "baseline_acceptance": baseline_acceptance,
        "overall_go_no_go": bool(overall_go),
        "claim_boundary": (
            "paired doc-11 acceptance on precision@top_rate; "
            "positive claim requires beating every baseline in the pool"
        ),
    }
