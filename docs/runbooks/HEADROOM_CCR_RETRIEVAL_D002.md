# HEADROOM_CCR_RETRIEVAL_D002 runbook

## Purpose

Run the Headroom CCR/MCP evidence cards that test recoverability via
`headroom_retrieve`. This is the next iteration after D001 and should be read
together with the D001 cards.

## Commands

```bash
uv sync --extra dev
HEADROOM_TELEMETRY=off uv run python scripts/claimbound_run_headroom_ccr_retrieval.py --access-date 2026-06-23
uv run python scripts/claimbound_render_evidence_card_svg.py docs/evidence_cards
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

The runner bootstraps the required public packages with:

```bash
uv run --with headroom-ai==0.27.0 --with transformers --with mcp python scripts/claimbound_run_headroom_ccr_retrieval.py
```

## Expected cards

- `HEADROOM_CCR_SOURCE_BOUNDARY_D002`
- `HEADROOM_CCR_MCP_FULL_RETRIEVE_D002`
- `HEADROOM_CCR_MCP_QUERY_RETRIEVE_D002`
- `HEADROOM_DIRECT_COMPRESS_NOT_CCR_D002`

## Interpretation

A pass on these cards does not mean Headroom always gives identical answers.
It means the documented local CCR/MCP recovery mechanism worked under this
protocol.

A D001 negative exact-answer card does not mean Headroom is unusable. It means
the strict direct-compress path without retrieve did not satisfy the exact
answer gate for that fixture.

For independent reproduction, rerun the commands above and submit a PR with
new cards or artifacts. Acceptable outcomes are `REPRODUCED_OUTCOME`,
`NEGATIVE_RESULT_UNDER_PROTOCOL` or `INSUFFICIENT_COVERAGE`, depending on the
observed result and protocol match.

