# NASA issue #151: 50-card source-boundary batch

- Access date: `2026-07-16`
- Operator: `NeoZorK`
- Matrix version: `2026-07-16`
- Matrix SHA-256: `a909b5f6d6f5264111f7d945cda22f146a8318eec184b3ee83a2ebe43416ccca`
- Batch summary SHA-256: `bf6ab44f4301805154cfb895ffd6b7a053cf169e41ec9939701d56c4346eada9`
- Raw HTML committed: `false`

## Result counts

- `INSUFFICIENT_COVERAGE`: 38
- `PASSED_UNDER_PROTOCOL`: 12

## Boundary

Each card records one frozen string-presence source-boundary gate against one official NASA mission page. A passed card does not validate scientific accuracy, mission performance, completeness, safety or operational suitability.

## Local validation

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
