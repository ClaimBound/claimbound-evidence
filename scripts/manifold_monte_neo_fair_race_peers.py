"""ManifoldBT peers for MANIFOLD_MONTE_NEO_FAIR_RACE_D001 (Community CPU)."""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any

import pandas as pd


def manifold_type_c(data: pd.DataFrame, combos: int = 256) -> dict[str, Any]:
    import manifoldbt as bt
    from manifoldbt.indicators import close, sma

    df = data.copy()
    root = tempfile.mkdtemp(prefix="mbt_fair_")
    store = bt.import_dataframe(
        df,
        symbol="RACE",
        symbol_id=1,
        interval="1m",
        data_root=root,
        metadata_db=os.path.join(root, "metadata.sqlite"),
    )
    start = df["timestamp"].min().strftime("%Y-%m-%d")
    end = (df["timestamp"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    s, e = bt.time_range(start, end)
    fast_vals = list(range(5, 18))
    slow_vals = list(range(30, 46))
    while len(fast_vals) * len(slow_vals) > combos and len(slow_vals) > 1:
        slow_vals = slow_vals[:-1]
    while len(fast_vals) * len(slow_vals) > combos and len(fast_vals) > 1:
        fast_vals = fast_vals[:-1]
    fast_p = bt.param("fast", default=fast_vals[0])
    slow_p = bt.param("slow", default=slow_vals[0])
    signal = bt.when(sma(close, fast_p) > sma(close, slow_p), 1.0, 0.0)
    strategy = bt.Strategy.create("fair_c").signal("signal", signal).size(signal * 0.25)
    cfg = bt.BacktestConfig(
        initial_capital=100_000.0, warmup_bars=60, time_range_start=s, time_range_end=e
    )
    t0 = time.perf_counter()
    sweep = bt.run_sweep(strategy, {"fast": fast_vals, "slow": slow_vals}, cfg, store)
    elapsed = time.perf_counter() - t0
    n = len(fast_vals) * len(slow_vals)
    return {
        "ok": True,
        "engine": "manifoldbt",
        "device": "cpu",
        "combos": n,
        "elapsed_s": elapsed,
        "combos_per_s": n / elapsed if elapsed > 0 else 0.0,
        "sweep_repr": str(sweep),
        "manifoldbt_version": getattr(bt, "__version__", "unknown"),
    }


def manifold_type_a(data: pd.DataFrame, n_sim: int = 1000, seed: int = 7) -> dict[str, Any]:
    import manifoldbt as bt
    from manifoldbt.indicators import close, sma
    from manifoldbt.plot import monte_carlo

    df = data.copy()
    root = tempfile.mkdtemp(prefix="mbt_fair_a_")
    store = bt.import_dataframe(
        df,
        symbol="RACE",
        symbol_id=1,
        interval="1m",
        data_root=root,
        metadata_db=os.path.join(root, "m.sqlite"),
    )
    start = df["timestamp"].min().strftime("%Y-%m-%d")
    end = (df["timestamp"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    s, e = bt.time_range(start, end)
    signal = bt.when(sma(close, 20) > sma(close, 50), 1.0, 0.0)
    strategy = bt.Strategy.create("fair_a").signal("signal", signal).size(signal * 0.25)
    cfg = bt.BacktestConfig(
        initial_capital=100_000.0, warmup_bars=60, time_range_start=s, time_range_end=e
    )
    result = bt.run(strategy, cfg, store)
    t0 = time.perf_counter()
    try:
        fig = monte_carlo(
            result, n_simulations=n_sim, method="bootstrap", seed=seed, show=False
        )
        elapsed = time.perf_counter() - t0
        _ = fig
        return {
            "ok": True,
            "engine": "manifoldbt",
            "device": "cpu",
            "method": "bootstrap",
            "n_simulations": n_sim,
            "elapsed_s": elapsed,
            "sims_per_s": n_sim / elapsed if elapsed > 0 else 0.0,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "engine": "manifoldbt",
            "device": "cpu",
            "error": str(exc),
            "n_simulations": n_sim,
        }


def manifold_type_b(data: pd.DataFrame, n_scenarios: int = 1000) -> dict[str, Any]:
    import manifoldbt as bt
    from manifoldbt.indicators import close, sma

    df = data.copy()
    root = tempfile.mkdtemp(prefix="mbt_fair_b_")
    store = bt.import_dataframe(
        df,
        symbol="RACE",
        symbol_id=1,
        interval="1m",
        data_root=root,
        metadata_db=os.path.join(root, "m.sqlite"),
    )
    start = df["timestamp"].min().strftime("%Y-%m-%d")
    end = (df["timestamp"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    s, e = bt.time_range(start, end)
    signal = bt.when(sma(close, 20) > sma(close, 50), 1.0, 0.0)
    strategy = bt.Strategy.create("fair_b").signal("signal", signal).size(signal * 0.25)
    cfg = bt.BacktestConfig(
        initial_capital=100_000.0, warmup_bars=60, time_range_start=s, time_range_end=e
    )
    bt.run(strategy, cfg, store)
    reps = min(50, n_scenarios)
    t0 = time.perf_counter()
    for _ in range(reps):
        bt.run(strategy, cfg, store)
    elapsed = time.perf_counter() - t0
    rate = reps / elapsed if elapsed > 0 else 0.0
    return {
        "ok": True,
        "engine": "manifoldbt",
        "device": "cpu",
        "scenarios": n_scenarios,
        "timed_reps": reps,
        "elapsed_s_for_reps": elapsed,
        "scenarios_per_s": rate,
        "note": (
            "Type B Manifold peer = repeated bt.run throughput proxy on identical bars "
            "(not Metal scenario MC)."
        ),
    }
