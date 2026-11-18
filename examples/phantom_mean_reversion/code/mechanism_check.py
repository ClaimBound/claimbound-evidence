#!/usr/bin/env python3
"""Mechanism check for Section 2 of the preprint (numpy only).

For rolling OLS (w = 100) on independent random walks it reports (i) the slope of the in-sample residual s_t on the
one-step-ahead residual e_t = y_t - beta_{t-1} x_t - alpha_{t-1}, and (ii) the correlation of s_{t-1} with e_t.
Usage: python3 mechanism_check.py [--paths 400] [--bars 5000] [--seed 20261015]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phantom_mr_sim import rolling_ols  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--paths", type=int, default=400)
ap.add_argument("--bars", type=int, default=5000)
ap.add_argument("--seed", type=int, default=20261015)
args = ap.parse_args()
w = 100
rng = np.random.default_rng(args.seed)
x = np.cumsum(0.01 * rng.standard_normal((args.paths, args.bars)), axis=1)
y = np.cumsum(0.01 * rng.standard_normal((args.paths, args.bars)), axis=1)
a, b, _ = rolling_ols(y, x, w)
s = y - b * x - a
e = np.full_like(s, np.nan)
e[:, 1:] = y[:, 1:] - b[:, :-1] * x[:, 1:] - a[:, :-1]
sl = slice(w + 1, None)
slope = np.array([(s[i, sl] * e[i, sl]).sum() / (e[i, sl] ** 2).sum() for i in range(args.paths)])
corr = np.array([np.corrcoef(s[i, w:-1], e[i, w + 1:])[0, 1] for i in range(args.paths)])
print("slope of s_t on e_t: mean %.3f (5-95%%: %.3f-%.3f)" % (slope.mean(), *np.percentile(slope, [5, 95])))
print("corr(s_{t-1}, e_t): mean %.3f (5-95%%: %.3f-%.3f)" % (corr.mean(), *np.percentile(corr, [5, 95])))
