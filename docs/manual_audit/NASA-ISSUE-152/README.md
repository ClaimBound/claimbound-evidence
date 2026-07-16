# NASA issue #152: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `67aa5a5c107a8f11ce511c6e736c206ebf23fca71fe811e10c15643965551105`
- Batch summary SHA-256: `0271c6fba6f88515e76c06f84a25da426d1cb848d904f41e6d0eb84b18e954d1`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 48
- `PASSED_UNDER_PROTOCOL`: 2

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
