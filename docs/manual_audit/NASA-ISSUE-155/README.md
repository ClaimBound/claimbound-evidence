# NASA issue #155: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `db2c6a9021c431cfbf98e7f0625f9e4c98d4090e1f475a4632e5adb328d7cd60`
- Batch summary SHA-256: `0b5643e477d29b216d6c7320192eb8a194b41537d5c002968c92357e5a74fc99`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 44
- `PASSED_UNDER_PROTOCOL`: 6

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
