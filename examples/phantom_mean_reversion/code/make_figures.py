#!/usr/bin/env python3
"""Figures for the preprint. Needs numpy + matplotlib. Usage: python3 make_figures.py results.json figures/"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phantom_mr_sim import run

res = json.load(open(sys.argv[1]))["results"]
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
w = [r["window"] for r in res]
fig, ax = plt.subplots(figsize=(6, 3.6))
for key, lab, mk in (("buggy", "spread-change accounting (wrong)", "o"), ("true", "leg accounting (correct)", "s")):
    med = [r["sharpe_%s_median" % key] for r in res]
    lo = [r["sharpe_%s_p05" % key] for r in res]
    hi = [r["sharpe_%s_p95" % key] for r in res]
    ax.plot(w, med, marker=mk, label=lab, color="black" if key == "buggy" else "0.55")
    ax.fill_between(w, lo, hi, color="0.85" if key == "buggy" else "0.93")
ax.axhline(0, color="0.3", lw=0.6)
ax.set_xscale("log"); ax.set_xticks(w); ax.set_xticklabels([str(v) for v in w])
ax.set_xlabel("rolling hedge-ratio window (bars)"); ax.set_ylabel("annualized Sharpe (hourly bars)")
ax.set_title("Independent random walks: median and 5-95% band over 400 pairs", fontsize=9)
ax.legend(fontsize=8, frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(out, "fig1_sharpe_vs_window.pdf")); fig.savefig(os.path.join(out, "fig1_sharpe_vs_window.png"), dpi=160)

_, bug, true = run(1, 5000, 100, 20261015)
fig, ax = plt.subplots(figsize=(6, 3.2))
ax.plot(np.cumsum(bug), color="black", label="booked (spread-change) P&L")
ax.plot(np.cumsum(true), color="0.55", label="tradable (leg) P&L")
ax.plot(np.cumsum(bug - true), color="black", ls=":", label="phantom term")
ax.set_xlabel("bar"); ax.set_ylabel("cumulative log P&L per unit notional")
ax.set_title("One pair of independent random walks, window 100", fontsize=9)
ax.legend(fontsize=8, frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(out, "fig2_example_path.pdf")); fig.savefig(os.path.join(out, "fig2_example_path.png"), dpi=160)
print("figures written")
