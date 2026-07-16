# NASA 500-card evidence atlas

The NASA campaign completes the 500 candidates frozen in issues `#147` through
`#156`: 50 selected official NASA pages × 10 narrow source-boundary gates.

## Result

| Measure | Count |
| --- | ---: |
| Evidence cards | 500 |
| Official pages fetched | 50 |
| HTTP 200 responses | 50 |
| Blocked sources | 0 |
| `PASSED_UNDER_PROTOCOL` | 65 |
| `INSUFFICIENT_COVERAGE` | 435 |

The local run keeps raw HTML outside the repository. Each committed batch
summary records the selected URL, canonical URL, HTTP status, access date and
SHA-256. A pass means only that all frozen lexical terms for that one candidate
appeared on that one page; it is not a NASA endorsement, a mission assessment or
a scientific finding.

Slot `10` is an overclaim/later-drift boundary. Its 50 cards deliberately remain
`INSUFFICIENT_COVERAGE`: absence of a bad interpretation cannot honestly be
turned into an automatic positive result.

## Rebuild

```bash
uv run python scripts/claimbound_run_nasa_factory.py --issue 147 check
uv run python scripts/build_nasa_factory_atlas.py
uv run claimbound validate-all
uv run --extra dev pytest -q
```

The dependency-free interactive atlas is in [atlas/index.html](atlas/index.html).
