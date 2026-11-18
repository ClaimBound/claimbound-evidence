#!/usr/bin/env python3
"""Draw docs/assets/protocolith/phantom-chart.svg from examples/phantom_mean_reversion/results.json (stdlib only).

    python3 scripts/build_phantom_chart.py

Bars: median Sharpe of the booked (rolling-hedge) series and of the tradable series for each window.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "examples" / "phantom_mean_reversion" / "results.json"
OUT = ROOT / "docs" / "assets" / "protocolith" / "phantom-chart.svg"
W, H = 760, 380
L, R, T, B = 70, 30, 70, 60
BOOKED, TRADABLE, INK, GRID, BG = "#e8b04a", "#5aa0d8", "#1c2733", "#d5dde6", "#f7f9fb"


def main() -> int:
    rows = json.loads(SRC.read_text(encoding="utf-8"))["results"]
    ymax = 16.0
    ymin = -2.0
    plot_h = H - T - B
    plot_w = W - L - R

    def y(v: float) -> float:
        return T + plot_h * (ymax - v) / (ymax - ymin)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
        '<title id="t">Phantom mean reversion: booked and tradable Sharpe by window</title>',
        '<desc id="d">Median Sharpe ratio of a rolling-hedge spread book and of the P&amp;L that holds the previous hedge, for five '
        "windows, on independent random walks. The booked bars are high; the tradable bars are near zero.</desc>",
        f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>',
        f'<text x="{L}" y="30" font-family="system-ui,sans-serif" font-size="18" font-weight="700" fill="{INK}">'
        "Same paths, two accounting rules</text>",
        f'<text x="{L}" y="50" font-family="system-ui,sans-serif" font-size="12" fill="#52606e">'
        "Median Sharpe on independent random walks, seed 20261015, 400 paths of 5000 bars</text>",
    ]
    for tick in range(-2, 17, 2):
        yy = y(tick)
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="{1.5 if tick == 0 else 0.7}"/>')
        out.append(f'<text x="{L - 8}" y="{yy + 4:.1f}" text-anchor="end" font-family="system-ui,sans-serif" font-size="11" fill="#52606e">{tick}</text>')
    group = plot_w / len(rows)
    bar = group * 0.32
    for i, row in enumerate(rows):
        cx = L + group * (i + 0.5)
        for dx, key, colour in ((-bar, "sharpe_buggy_median", BOOKED), (0, "sharpe_true_median", TRADABLE)):
            v = float(row[key])
            top, base = y(max(v, 0)), y(min(v, 0))
            out.append(f'<rect x="{cx + dx:.1f}" y="{top:.1f}" width="{bar:.1f}" height="{max(base - top, 1.5):.1f}" fill="{colour}"/>')
            ty = top - 5 if v >= 0 else base + 13
            out.append(
                f'<text x="{cx + dx + bar / 2:.1f}" y="{ty:.1f}" text-anchor="middle" font-family="system-ui,sans-serif" '
                f'font-size="11" fill="{INK}">{v:+.2f}</text>'
            )
        out.append(
            f'<text x="{cx:.1f}" y="{H - B + 20}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="12" fill="{INK}">'
            f'window {row["window"]}</text>'
        )
    lx = W - R - 250
    out.append(f'<rect x="{lx}" y="14" width="12" height="12" fill="{BOOKED}"/><text x="{lx + 18}" y="25" font-family="system-ui,sans-serif" font-size="12" fill="{INK}">booked (rolling hedge)</text>')
    out.append(f'<rect x="{lx + 175}" y="14" width="12" height="12" fill="{TRADABLE}"/><text x="{lx + 193}" y="25" font-family="system-ui,sans-serif" font-size="12" fill="{INK}">tradable</text>')
    out.append("</svg>")
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
