#!/usr/bin/env python3
"""Phantom mean reversion: rolling-hedge spread accounting on independent random walks.

Reproduces every number in the preprint. Requires only numpy.
Usage: python3 phantom_mr_sim.py [--paths 400] [--bars 5000] [--seed 20261015] [--out results.json]
"""
import argparse
import json

import numpy as np

BARS_PER_YEAR = 8760  # hourly bars, 24/7 market


def rolling_ols(y, x, w):
    """OLS y = a + b x over the trailing window [t-w+1, t] (inclusive, no look-ahead). Arrays (P, T)."""
    def rsum(a):
        c = np.cumsum(a, axis=1)
        out = np.full_like(a, np.nan)
        out[:, w - 1] = c[:, w - 1]
        out[:, w:] = c[:, w:] - c[:, :-w]
        return out
    sx, sy = rsum(x), rsum(y)
    sxx, sxy, syy = rsum(x * x), rsum(x * y), rsum(y * y)
    vx = sxx - sx * sx / w
    b = (sxy - sx * sy / w) / vx
    a = (sy - b * sx) / w
    # residual variance inside the window
    rss = syy - sy * sy / w - b * (sxy - sx * sy / w)
    sd = np.sqrt(np.maximum(rss / (w - 2), 1e-18))
    return a, b, sd


def positions(z, entry=2.0, exit_=0.5):
    """Classic z-score state machine on the spread: short spread when z>entry, long when z<-entry, flat when |z|<exit."""
    P, T = z.shape
    pos = np.zeros((P, T))
    cur = np.zeros(P)
    for t in range(T):
        zt = z[:, t]
        ok = np.isfinite(zt)
        cur = np.where(ok & (cur == 0) & (zt > entry), -1.0, cur)
        cur = np.where(ok & (cur == 0) & (zt < -entry), 1.0, cur)
        cur = np.where(ok & (cur != 0) & (np.abs(zt) < exit_), 0.0, cur)
        cur = np.where(ok, cur, 0.0)
        pos[:, t] = cur
    return pos


def sharpe(r):
    m, s = np.nanmean(r, axis=1), np.nanstd(r, axis=1)
    return np.where(s > 0, m / s * np.sqrt(BARS_PER_YEAR), 0.0)


def run(paths, bars, w, seed, sigma=0.01):
    rng = np.random.default_rng(seed)
    x = np.cumsum(sigma * rng.standard_normal((paths, bars)), axis=1)  # log price leg 1
    y = np.cumsum(sigma * rng.standard_normal((paths, bars)), axis=1)  # log price leg 2, independent
    a, b, sd = rolling_ols(y, x, w)
    s = y - b * x - a                      # spread with the hedge re-estimated every bar
    z = s / sd
    pos = positions(z)
    p_prev = np.zeros_like(pos)
    p_prev[:, 1:] = pos[:, :-1]
    ds = np.zeros_like(s)
    ds[:, 1:] = s[:, 1:] - s[:, :-1]
    b_prev = np.full_like(b, np.nan)
    b_prev[:, 1:] = b[:, :-1]
    dx = np.zeros_like(x)
    dx[:, 1:] = np.diff(x, axis=1)
    dy = np.zeros_like(y)
    dy[:, 1:] = np.diff(y, axis=1)
    pnl_bug = p_prev * ds                                  # what the buggy backtest books
    pnl_true = p_prev * (dy - b_prev * dx)                 # what a trader holding the t-1 hedge earns
    start = w + 1
    pnl_bug, pnl_true = pnl_bug[:, start:], pnl_true[:, start:]
    pnl_bug = np.nan_to_num(pnl_bug)
    pnl_true = np.nan_to_num(pnl_true)
    phantom = pnl_bug - pnl_true
    sb, st = sharpe(pnl_bug), sharpe(pnl_true)
    return {
        "window": w,
        "paths": paths,
        "bars": bars,
        "sharpe_buggy_median": float(np.median(sb)),
        "sharpe_buggy_p05": float(np.percentile(sb, 5)),
        "sharpe_buggy_p95": float(np.percentile(sb, 95)),
        "share_buggy_positive": float(np.mean(sb > 0)),
        "sharpe_true_median": float(np.median(st)),
        "sharpe_true_p05": float(np.percentile(st, 5)),
        "sharpe_true_p95": float(np.percentile(st, 95)),
        "share_true_positive": float(np.mean(st > 0)),
        "phantom_share_of_buggy_pnl": float(np.sum(phantom) / np.sum(pnl_bug)),
        "time_in_market": float(np.mean(p_prev[:, start:] != 0)),
    }, pnl_bug[0], pnl_true[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=400)
    ap.add_argument("--bars", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261015)
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--series-dir", default=None, help="write example return series (path 0, window 100) as CSV")
    args = ap.parse_args()
    rows = []
    for w in (30, 60, 100, 250, 500):
        res, bug, true = run(args.paths, args.bars, w, args.seed)
        rows.append(res)
        print("w=%3d  buggy median Sharpe %+6.2f (p05 %+5.2f, positive %3.0f%%)   true median %+5.2f (positive %3.0f%%)   phantom share %.2f"
              % (w, res["sharpe_buggy_median"], res["sharpe_buggy_p05"], 100 * res["share_buggy_positive"],
                 res["sharpe_true_median"], 100 * res["share_true_positive"], res["phantom_share_of_buggy_pnl"]))
        if args.series_dir and w == 100:
            import os
            os.makedirs(args.series_dir, exist_ok=True)
            hours = np.arange(bug.size)
            for name, r in (("buggy", bug), ("true", true)):
                with open(os.path.join(args.series_dir, "returns_%s.csv" % name), "w") as f:
                    f.write("date,return\n")
                    t0 = np.datetime64("2024-01-01T00:00")
                    for h, v in zip(hours, r):
                        f.write("%s,%.10f\n" % (str(t0 + np.timedelta64(int(h), "h")), v))
    with open(args.out, "w") as f:
        json.dump({"seed": args.seed, "bars_per_year": BARS_PER_YEAR, "results": rows}, f, indent=2)


if __name__ == "__main__":
    main()
