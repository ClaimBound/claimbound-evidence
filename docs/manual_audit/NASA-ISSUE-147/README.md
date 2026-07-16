# NASA issue #147: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `9b8c3a6415cea2ad0e7bc74e49c14e3c78753c3bd1d7da611a47647080fba53e`
- Batch summary SHA-256: `6dab3f1cc7275fcb4039999ca965d8807536f41fef61b4beb3f8f177319dcfce`
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
