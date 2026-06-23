# HEADROOM_SEMANTIC_FIDELITY_D004 runbook

## Commands

```bash
uv sync --extra dev
HEADROOM_TELEMETRY=off uv run python scripts/claimbound_run_headroom_semantic_fidelity.py --access-date 2026-06-23
uv run python scripts/claimbound_render_evidence_card_svg.py --all docs/evidence_cards
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

The runner bootstraps public runtime dependencies with:

```bash
uv run --with headroom-ai==0.27.0 --with transformers python scripts/claimbound_run_headroom_semantic_fidelity.py
```

## Expected interpretation

D004 does not ask whether the exact text is the same. It asks whether the same
structured meaning survives compression under the local Ollama protocol.

If a card is negative, read the sanitized summary:

- `baseline_semantic_match=true` means the original context/model could solve
  the task.
- `compressed_semantic_match=false` means compression changed or removed facts
  needed by the answer.
- `compressed_semantic_match=true` with low reduction means meaning survived but
  the savings claim did not pass.

## LinkedIn note

Do not use this Headroom track as the first LinkedIn article example yet. The
mixed outcomes are useful internally, but a public launch article should use a
cleaner example with less protocol nuance.

