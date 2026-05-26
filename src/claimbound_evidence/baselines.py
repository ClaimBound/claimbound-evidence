# SPDX-License-Identifier: Apache-2.0

"""Pure-numpy doc-11 baseline pool for ClaimBound non-PnL anomaly/regime evaluation.

Each baseline produces a causal, train-only-normalized outlier score over a
closing-price series. Higher score = more anomalous. Outputs are aligned
with the input series and ready to be compared against ClaimBound feature-group
scores under paired acceptance gates (doc 11 / doc 53).

Six reference baselines, all deterministic, NumPy-only, no lookahead:
``zscore_rolling``, ``ewma_residual``, ``stl_residual``,
``persistence_residual``, ``knn_lof``, ``isolation_tree``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

DOC11_BASELINE_NAMES: tuple[str, ...] = (
    "zscore_rolling",
    "ewma_residual",
    "stl_residual",
    "persistence_residual",
    "knn_lof",
    "isolation_tree",
)


@dataclass(frozen=True)
class BaselinePoolConfig:
    """Deterministic configuration for the doc-11 baseline pool.

    All defaults are chosen to be reasonable without peeking at test data.
    """

    zscore_lookback: int = 50
    ewma_alpha: float = 0.1
    stl_period: int = 7
    stl_trend_window: int = 25
    knn_window: int = 50
    knn_k: int = 5
    isolation_window: int = 50
    isolation_trees: int = 32
    isolation_max_depth: int = 8
    rng_seed: int = 1337


def _log_returns(prices: NDArray[np.float64]) -> NDArray[np.float64]:
    values = np.asarray(prices, dtype=np.float64)
    log_p = np.log(np.where(values > 0.0, values, np.nan))
    out = np.zeros(len(values), dtype=np.float64)
    if len(values) < 2:
        return out
    out[1:] = log_p[1:] - log_p[:-1]
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def zscore_rolling_score(
    prices: NDArray[np.float64],
    *,
    lookback: int,
) -> NDArray[np.float64]:
    """Rolling absolute zscore of log-returns (causal, no lookahead)."""

    ret = _log_returns(prices)
    out = np.zeros_like(ret)
    if lookback <= 1 or len(ret) == 0:
        return out
    for i in range(len(ret)):
        start = max(0, i - lookback + 1)
        window = ret[start : i + 1]
        if len(window) < 2:
            continue
        mu = float(np.mean(window[:-1])) if len(window) >= 2 else 0.0
        sigma = float(np.std(window[:-1])) if len(window) >= 2 else 0.0
        if sigma <= 1.0e-12:
            sigma = 1.0
        out[i] = abs(ret[i] - mu) / sigma
    return out


def ewma_residual_score(
    prices: NDArray[np.float64],
    *,
    alpha: float,
) -> NDArray[np.float64]:
    """Absolute residual against a one-sided EWMA of log-returns."""

    ret = _log_returns(prices)
    out = np.zeros_like(ret)
    if len(ret) == 0:
        return out
    ewma = 0.0
    for i in range(len(ret)):
        out[i] = abs(ret[i] - ewma)
        ewma = (1.0 - alpha) * ewma + alpha * ret[i]
    return out


def stl_residual_score(
    prices: NDArray[np.float64],
    *,
    period: int,
    trend_window: int,
) -> NDArray[np.float64]:
    """Simplified additive trend/seasonal/residual decomposition.

    Trend is a causal centered-aware moving average over ``trend_window``;
    seasonal component is the mean residual-from-trend at the same phase of
    ``period`` over the in-window history preceding bar ``i``. The score is
    the absolute residual after removing trend and seasonal estimates.
    """

    ret = _log_returns(prices)
    out = np.zeros_like(ret)
    if period <= 1 or trend_window <= 1 or len(ret) == 0:
        return np.abs(ret)
    trend = np.zeros_like(ret)
    for i in range(len(ret)):
        start = max(0, i - trend_window + 1)
        window = ret[start : i + 1]
        trend[i] = float(np.mean(window)) if len(window) else 0.0
    detrended = ret - trend
    seasonal = np.zeros_like(ret)
    for i in range(len(ret)):
        phase = i % period
        history_end = i
        idx = np.arange(phase, history_end, period, dtype=np.int64)
        if len(idx) == 0:
            continue
        seasonal[i] = float(np.mean(detrended[idx]))
    residual = ret - trend - seasonal
    out = np.abs(residual)
    return out


def persistence_residual_score(prices: NDArray[np.float64]) -> NDArray[np.float64]:
    """Absolute one-step log-return (the canonical persistence/random-walk residual)."""

    return np.abs(_log_returns(prices))


def knn_lof_score(
    prices: NDArray[np.float64],
    *,
    window: int,
    k: int,
) -> NDArray[np.float64]:
    """Local-Outlier-Factor approximation on sliding windows of log-returns.

    For bar ``i`` the method takes the preceding ``window`` log-returns (open
    interval ending before ``i``) as points in a 1-D feature space together
    with the target value ``ret[i]``, then computes the ratio of the target
    point's k-NN mean distance to the median k-NN mean distance of the
    reference points. The ratio is monotonically increasing in how far the
    target sits from the local density — a deterministic LOF-style proxy.
    """

    ret = _log_returns(prices)
    out = np.zeros_like(ret)
    if window <= k + 1 or len(ret) == 0:
        return out
    for i in range(len(ret)):
        start = max(0, i - window)
        ref = ret[start:i]
        if len(ref) <= k:
            continue
        target = ret[i]
        target_dists = np.sort(np.abs(ref - target))
        target_kmean = float(np.mean(target_dists[:k]))
        ref_kmeans = np.empty(len(ref), dtype=np.float64)
        for j in range(len(ref)):
            others = np.delete(ref, j)
            if len(others) < k:
                ref_kmeans[j] = 0.0
                continue
            od = np.sort(np.abs(others - ref[j]))
            ref_kmeans[j] = float(np.mean(od[:k]))
        median_ref = float(np.median(ref_kmeans)) if len(ref_kmeans) else 0.0
        if median_ref <= 1.0e-12:
            median_ref = 1.0
        out[i] = target_kmean / median_ref
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def isolation_tree_score(
    prices: NDArray[np.float64],
    *,
    window: int,
    n_trees: int,
    max_depth: int,
    rng_seed: int,
) -> NDArray[np.float64]:
    """Deterministic isolation-forest-style isolation depth on log-returns.

    For each bar ``i`` the method samples the preceding ``window`` log-returns
    as a reference cloud and grows ``n_trees`` random axis-aligned binary
    trees up to ``max_depth``. The target point's isolation depth averaged
    across trees is returned and inverted so that lower depth (easier to
    isolate, hence more anomalous) maps to a higher score.
    """

    ret = _log_returns(prices)
    out = np.zeros_like(ret)
    if window <= 2 or n_trees <= 0 or max_depth <= 0 or len(ret) == 0:
        return out
    rng = np.random.default_rng(rng_seed)
    for i in range(len(ret)):
        start = max(0, i - window)
        ref = ret[start:i]
        if len(ref) < 2:
            continue
        target = ret[i]
        depths = np.empty(n_trees, dtype=np.float64)
        for t in range(n_trees):
            lo = float(np.min(ref))
            hi = float(np.max(ref))
            active = ref.copy()
            depth = 0.0
            for _ in range(max_depth):
                if hi - lo <= 1.0e-12 or len(active) <= 1:
                    break
                split = rng.uniform(lo, hi)
                if target < split:
                    active = active[active < split]
                    hi = split
                else:
                    active = active[active >= split]
                    lo = split
                depth += 1.0
                if len(active) == 0:
                    break
            depths[t] = depth
        mean_depth = float(np.mean(depths))
        out[i] = float(max_depth) - mean_depth
    return out


def compute_baseline_scores(
    prices: NDArray[np.float64],
    *,
    config: BaselinePoolConfig,
) -> dict[str, NDArray[np.float64]]:
    """Compute all six doc-11 baseline score series (aligned with ``prices``)."""

    prices_arr = np.asarray(prices, dtype=np.float64)
    return {
        "zscore_rolling": zscore_rolling_score(prices_arr, lookback=config.zscore_lookback),
        "ewma_residual": ewma_residual_score(prices_arr, alpha=config.ewma_alpha),
        "stl_residual": stl_residual_score(
            prices_arr,
            period=config.stl_period,
            trend_window=config.stl_trend_window,
        ),
        "persistence_residual": persistence_residual_score(prices_arr),
        "knn_lof": knn_lof_score(
            prices_arr,
            window=config.knn_window,
            k=config.knn_k,
        ),
        "isolation_tree": isolation_tree_score(
            prices_arr,
            window=config.isolation_window,
            n_trees=config.isolation_trees,
            max_depth=config.isolation_max_depth,
            rng_seed=config.rng_seed,
        ),
    }


def normalize_baseline_score(
    values: NDArray[np.float64],
    train_idx: NDArray[np.int64],
    test_idx: NDArray[np.int64],
) -> NDArray[np.float64]:
    """Zero-mean/unit-variance normalization using train-only statistics."""

    arr = np.asarray(values, dtype=np.float64)
    train = arr[train_idx]
    mean = float(np.mean(train)) if len(train) else 0.0
    std = float(np.std(train)) if len(train) else 0.0
    if std <= 1.0e-12:
        std = 1.0
    scaled = (arr[test_idx] - mean) / std
    return np.nan_to_num(scaled, nan=0.0, posinf=0.0, neginf=0.0)
