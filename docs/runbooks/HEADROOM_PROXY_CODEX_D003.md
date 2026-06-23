# HEADROOM_PROXY_CODEX_D003 runbook

## Commands

```bash
uv sync --extra dev
HEADROOM_TELEMETRY=off uv run python scripts/claimbound_run_headroom_proxy_codex.py --access-date 2026-06-23
uv run python scripts/claimbound_render_evidence_card_svg.py --all docs/evidence_cards
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

The runner bootstraps public runtime dependencies with:

```bash
uv run --with headroom-ai==0.27.0 --with transformers --with fastapi --with httpx --with uvicorn python scripts/claimbound_run_headroom_proxy_codex.py
```

## Expected interpretation

- `HEADROOM_PROXY_COMPRESS_ENDPOINT_D003`: local proxy compression result.
- `HEADROOM_PROXY_CCR_HASH_RETRIEVE_D003`: whether that endpoint exposed a
  usable retrieve hash.
- `HEADROOM_CODEX_PROXY_BOUNDARY_D003`: Codex route surface only, not a Codex
  compatibility pass.

## Local Ollama utility

With Ollama, the primary benefit is not cloud cost reduction. The practical
benefit, if the workflow fits, is smaller prompt/context payloads and a better
chance of staying inside the local model context window. If an answer requires
details removed by compression, the workflow needs CCR/retrieve; otherwise the
compressed answer can drift.

