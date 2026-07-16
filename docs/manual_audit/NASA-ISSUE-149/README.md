# NASA issue #149: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `ad939eef517e02d13b4e5770e655155130b41ca6cd7258091d3048ca1aefcd6e`
- Batch summary SHA-256: `75c48e391c8a40a6ce7facce5d8eda696c3d5fe6d8d0cc1cd4fabe265087109b`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 40
- `PASSED_UNDER_PROTOCOL`: 10

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
