# ESA issue #135: 100-card source-boundary batch

- Access date: `2026-07-13`
- Operator: `NeoZorK`
- Matrix version: `2026-07-13`
- Matrix SHA-256: `9b3105cdb17def8761f9d6232fe1eec32e27bc4a0b4a62b98ffb7bb0093cf8fd`
- Batch summary SHA-256: `323c726dd27b2660faab97d732e336973fc296504f5d427310293c0391d5ee48`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 4
- `PASSED_UNDER_PROTOCOL`: 96

## Boundary

Each card records one frozen string-presence source-boundary gate against one official ESA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
