# MANIFOLD_MONTE_NEO_FAIR_RACE_D001 sanitized report

**result_status:** `PASSED_UNDER_PROTOCOL`

## Hardware

```json
{
  "os": "macOS-26.6.2-arm64-arm-64bit",
  "machine": "arm64",
  "chip": "Apple M1 Pro",
  "python": "3.12.11",
  "cuda_peer_on_host": false
}
```

## Type C — sweep (gate)

| engine | combos/s | ok |
|---|---:|---|
| monte_neo | 45977.35004482914 | True |
| manifoldbt | 37.95973972666864 | True |
| gate_pass | | True |

## Type A — return-path bootstrap

| engine | sims/s | ok |
|---|---:|---|
| monte_neo | 1854.5397909153814 | True |
| manifoldbt | 3203.7984234099463 | True |

## Type B — scenario / N-run

| engine | scenarios/s | ok |
|---|---:|---|
| monte_neo | 2298.891294181274 | True |
| manifoldbt | 1002.7525557635233 | True |

## Claim boundary

Under protocol MANIFOLD_MONTE_NEO_FAIR_RACE_D001 on recorded Apple Silicon hardware, comparing Monte-Neo (MIT) vs ManifoldBT Community CPU only. CUDA is not a peer. Type A/B/C are separate. Does not claim universal engine superiority.

## Charts

- `charts/type_c_combos_per_s.png`
- `charts/type_a_sims_per_s.png`
- `charts/type_b_scenarios_per_s.png`
