# NASA issue #156: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `3386c0a84ba119cfdc10a91aa6ea78353cc5790c8038e1b301380c09f05c21c0`
- Batch summary SHA-256: `57ff4a3f4bacc1a670df2da4ffd28a6975bc1c4a606960d3ccd0139fb4346e96`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 45
- `PASSED_UNDER_PROTOCOL`: 5

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
