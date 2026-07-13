# ESA issue #134: 100-card source-boundary batch

- Access date: `2026-07-13`
- Operator: `NeoZorK`
- Matrix version: `2026-07-13`
- Matrix SHA-256: `5c56d12bae159c1026925fd1399e97190d3ef05e989c20e983c382be0fab1d2d`
- Batch summary SHA-256: `cd216f0a52ea2c8b067e666cf08d5cc59b4bf162a5630e21b9d1917bbe07551d`
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
