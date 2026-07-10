# ESA issue #131: 100-card source-boundary batch

- Access date: `2026-07-10`
- Operator: `NeoZorK`
- Matrix version: `1.0.0`
- Matrix SHA-256: `c748ff8592cad913dc43264be8571cc4c95894ddb3bd426b1d140598ba4f72a7`
- Batch summary SHA-256: `09ae8d43630ce6714ef0e14caa7743c12e866c83b8aa606ba04107bd9aeb2a55`
- Raw HTML committed: `false`

## Result counts

- `PASSED_UNDER_PROTOCOL`: 100

## Boundary

Each card records one frozen string-presence source-boundary gate against one official ESA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
