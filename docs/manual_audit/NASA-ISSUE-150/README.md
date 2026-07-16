# NASA issue #150: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `0c4810ef668f95efde489e989efd7f2a93815f25da613d463ede95416d44a28e`
- Batch summary SHA-256: `b132393af5de042eb9dba83d5024a13fbbc0929cd75a0d7c7ce72ffe62cea68d`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 43
- `PASSED_UNDER_PROTOCOL`: 7

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
