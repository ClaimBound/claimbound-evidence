# ESA issue #133: 100-card source-boundary batch

- Access date: `2026-07-13`
- Operator: `NeoZorK`
- Matrix version: `2026-07-13`
- Matrix SHA-256: `171e80fba5c4ecd3b3574a11c2081c9c12a4d45bf42bc7bebbf97b8f60922828`
- Batch summary SHA-256: `21415bc5e6ca087ff8f045f89a852c44237ae46b5e01a61a36c8ba67d7fb0c60`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 2
- `PASSED_UNDER_PROTOCOL`: 98

## Boundary

Each card records one frozen string-presence source-boundary gate against one official ESA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
