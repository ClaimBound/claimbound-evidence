# MANIFOLD_MONTE_NEO_FAIR_RACE_D001 — Pre-registration charter

**Protocol ID:** `MANIFOLD_MONTE_NEO_FAIR_RACE_D001`  
**Version:** `2026-09-12-v1`  
**Rule:** Rules first. Source second. Run third. Claim last.

## Intent

Narrow, honest performance comparison on **Apple Silicon CPU path for ManifoldBT**
(Community) versus **Monte-Neo** (MIT, Metal/Numba where applicable).

This protocol does **not** claim universal superiority of C++/Metal over Rust.

## Hardware / software pins (maintainer baseline)

- Host: Apple M1 Pro, 16 GB RAM, arm64
- Python: 3.12+ (baseline recorded 3.13.x)
- `manifoldbt==0.26.0` Community (CUDA unavailable on Apple Silicon)
- Monte-Neo: https://github.com/NeoZorK/Monte-Neo @ pinned SHA in evidence card
- Dataset: synthetic OHLCV, seed `42`, `n_bars=50000` (generator in runner)

## Comparison types (never mixed)

| Type | Meaning | Manifold peer | Monte-Neo peer |
|------|---------|---------------|----------------|
| C | Parameter sweep ≤256 | `bt.run_sweep` | `fused_sma_sweep` / fair_race Type C |
| A | Return-path MC ≤1000 | `bt.plot.monte_carlo` bootstrap timing | `return_path_bootstrap` on same returns |
| B | Scenario re-backtest ≤1000 | N× independent `bt.run` on same bars (throughput proxy) | Metal/MLX scenario batch |

## Acceptance gates (frozen before outcome inspection)

- **Type C:** both engines `ok`; `monte_neo.combos_per_s > manifold.combos_per_s`
- **Type A:** both engines `ok` (informational throughput; **no speed winner required** — Manifold may be faster on return-path MC)
- **Type B:** both engines `ok` (Monte-Neo may use Metal or documented CPU fallback; Manifold uses repeated `bt.run` proxy)

Overall card status:

- `PASSED_UNDER_PROTOCOL` if Type C gate passes and Type A both ok
- else `NEGATIVE_RESULT_UNDER_PROTOCOL`

## Reproduce (card-only)

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync
uv pip install "manifoldbt[plot]==0.26.0" matplotlib pandas pyarrow \
  "monte-neo @ git+https://github.com/NeoZorK/Monte-Neo.git@922631404496adc9b7abd02b1634ea04c155061e"
uv run python scripts/run_manifold_monte_neo_fair_race_d001.py \
  --out-dir artifacts/manifold_monte_neo_fair_race_d001
```

Pinned Monte-Neo branch for race helpers: `race/m1-metal-phase2` @ `922631404496adc9b7abd02b1634ea04c155061e`.

## Known limitations

- Manifold CUDA / Pro GPU is not a peer on Apple Silicon.
- Community sweep session caps: runner uses fresh process semantics where needed.
- Type A and Type B answer different scientific questions.
- Synthetic data only (no venue rights issues).
