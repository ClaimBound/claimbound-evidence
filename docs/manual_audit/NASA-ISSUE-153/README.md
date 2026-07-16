# NASA issue #153: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `5183ed1ce8ff0c9943c6c261c2177e2be6e6058848fc5ab5bc802f50e561fcab`
- Batch summary SHA-256: `418a7883f89d456ca036a82674a222f45b9c68d669e497aff7c203ccbbe2005b`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 42
- `PASSED_UNDER_PROTOCOL`: 8

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
