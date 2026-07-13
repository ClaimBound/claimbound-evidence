# ESA issue #132: 100-card source-boundary batch

- Access date: `2026-07-13`
- Operator: `NeoZorK`
- Matrix version: `2026-07-13`
- Matrix SHA-256: `5f0752762c67084805c7a4e14e8e947a50ef6dda5ad523465442ca9ba2942571`
- Batch summary SHA-256: `1c210df5ec9cf13459d977161f74a48a089a33665d6ddfae64d3495ba4ec501c`
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
