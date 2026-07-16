# NASA issue #148: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `e2847e68514df67a674cee0a4d4811fdc2ae82cb5ba63666b05991479cd8c419`
- Batch summary SHA-256: `4469d08ffc42af7b0d41430b98d5bf7c6bfc72cdbbc61c6f51f254c67693375e`
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
