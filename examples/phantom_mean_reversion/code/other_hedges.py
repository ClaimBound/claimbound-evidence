#!/usr/bin/env python3
"""Robustness runs for the preprint: other hedge estimators and a genuinely cointegrated pair (numpy only).

Usage: python3 other_hedges.py [--paths 400] [--bars 5000] [--seed 20261015] [--out results_other.json]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phantom_mr_sim import positions, rolling_ols, sharpe  # noqa: E402

WARM = 250


def ewma_ols(y, x, halflife):
    """Exponentially weighted OLS of y on x, updated with the observation at t (no look-ahead)."""
    lam = 0.5 ** (1.0 / halflife)
    paths, bars = y.shape
    a, b, sd = (np.zeros((paths, bars)) for _ in range(3))
    sw, sx, sy, sxx, sxy, syy = (np.zeros(paths) for _ in range(6))
    for t in range(bars):
        xt, yt = x[:, t], y[:, t]
        sw = lam * sw + 1.0
        sx, sy = lam * sx + xt, lam * sy + yt
        sxx, sxy, syy = lam * sxx + xt * xt, lam * sxy + xt * yt, lam * syy + yt * yt
        mx, my = sx / sw, sy / sw
        vx, cxy = sxx / sw - mx * mx, sxy / sw - mx * my
        bb = np.where(vx > 1e-12, cxy / np.maximum(vx, 1e-12), 0.0)
        a[:, t], b[:, t] = my - bb * mx, bb
        sd[:, t] = np.sqrt(np.maximum(syy / sw - my * my - bb * cxy, 1e-18))
    return a, b, sd


def kalman(y, x, delta, obs_var):
    """Random-walk state [alpha, beta] filtered with the observation at t; sd is the forecast-error sd."""
    paths, bars = y.shape
    a, b, sd = (np.zeros((paths, bars)) for _ in range(3))
    theta, cov = np.zeros((paths, 2)), np.tile(np.eye(2), (paths, 1, 1))
    state_var = delta / (1.0 - delta)
    for t in range(bars):
        if t > 0:
            cov = cov + np.eye(2) * state_var
        f = np.stack([np.ones(paths), x[:, t]], axis=1)
        q = np.einsum("pi,pij,pj->p", f, cov, f) + obs_var
        err = y[:, t] - (f * theta).sum(1)
        gain = np.einsum("pij,pj->pi", cov, f) / q[:, None]
        theta = theta + gain * err[:, None]
        cov = cov - np.einsum("pi,pj,pjk->pik", gain, f, cov)
        a[:, t], b[:, t], sd[:, t] = theta[:, 0], theta[:, 1], np.sqrt(q)
    return a, b, sd


def evaluate(y, x, fit):
    a, b, sd = fit(y, x)
    z = (y - b * x - a) / sd
    s = y - b * x - a
    z[:, :WARM] = np.nan
    pos = positions(z)
    q = np.zeros_like(pos)
    q[:, 1:] = pos[:, :-1]
    b_prev = np.zeros_like(b)
    b_prev[:, 1:] = b[:, :-1]
    ds, dx, dy = (np.zeros_like(s) for _ in range(3))
    ds[:, 1:], dx[:, 1:], dy[:, 1:] = np.diff(s, axis=1), np.diff(x, axis=1), np.diff(y, axis=1)
    booked = np.nan_to_num(q * ds)[:, WARM:]
    tradable = np.nan_to_num(q * (dy - b_prev * dx))[:, WARM:]
    sb, st = sharpe(booked), sharpe(tradable)
    total = booked.sum()
    return {
        "sharpe_booked_median": float(np.median(sb)), "share_booked_positive": float(np.mean(sb > 0)),
        "sharpe_tradable_median": float(np.median(st)), "share_tradable_positive": float(np.mean(st > 0)),
        "phantom_share_of_booked_pnl": float((booked - tradable).sum() / total) if total != 0 else None,
        "share_of_pairs_that_traded": float(np.mean(np.any(q[:, WARM:] != 0, axis=1))),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=400)
    ap.add_argument("--bars", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261015)
    ap.add_argument("--out", default="results_other.json")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    x = np.cumsum(0.01 * rng.standard_normal((args.paths, args.bars)), axis=1)
    y = np.cumsum(0.01 * rng.standard_normal((args.paths, args.bars)), axis=1)
    # A genuinely cointegrated pair: y = x + stationary AR(1) residual (phi = 0.95, innovation sd 0.01).
    e = np.zeros((args.paths, args.bars))
    inn = 0.01 * rng.standard_normal((args.paths, args.bars))
    for t in range(1, args.bars):
        e[:, t] = 0.95 * e[:, t - 1] + inn[:, t]
    yc = x + e
    runs = {
        "rolling OLS, window 100 (independent walks)": (y, lambda yy, xx: rolling_ols(yy, xx, 100)),
        "EWMA OLS, half-life 50": (y, lambda yy, xx: ewma_ols(yy, xx, 50)),
        "EWMA OLS, half-life 250": (y, lambda yy, xx: ewma_ols(yy, xx, 250)),
        "Kalman, delta 1e-5": (y, lambda yy, xx: kalman(yy, xx, 1e-5, 1e-4)),
        "Kalman, delta 1e-4": (y, lambda yy, xx: kalman(yy, xx, 1e-4, 1e-4)),
        "Kalman, delta 1e-3": (y, lambda yy, xx: kalman(yy, xx, 1e-3, 1e-4)),
        "rolling OLS, window 100 (cointegrated pair)": (yc, lambda yy, xx: rolling_ols(yy, xx, 100)),
        "rolling OLS, window 500 (cointegrated pair)": (yc, lambda yy, xx: rolling_ols(yy, xx, 500)),
    }
    out = {"seed": args.seed, "paths": args.paths, "bars": args.bars, "runs": {}}
    for name, (yy, fit) in runs.items():
        r = evaluate(yy, x, fit)
        out["runs"][name] = r
        share = r["phantom_share_of_booked_pnl"]
        print("%-46s booked %+6.2f (%3.0f%% pos)  tradable %+6.2f (%3.0f%% pos)  phantom share %s  traded %3.0f%%" % (
            name, r["sharpe_booked_median"], 100 * r["share_booked_positive"], r["sharpe_tradable_median"],
            100 * r["share_tradable_positive"], "n/a" if share is None else "%.2f" % share,
            100 * r["share_of_pairs_that_traded"]))
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
