# NASA issue #154: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `157350e6228b3b2b303c7d29476847b958f4410ee53d8ce3f3cbb8a2fb780378`
- Batch summary SHA-256: `2bd68c911afff6e73146759b078a9b79b0cf19c1b71f3744460151aa4a15a99a`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 46
- `PASSED_UNDER_PROTOCOL`: 4

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
