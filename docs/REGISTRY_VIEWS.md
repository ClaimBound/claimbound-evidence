# Registry views

Read-only static views of the public evidence registry, generated from
`docs/registry/evidence_index.json` into `docs/registry/views/`:

- `index.html` - one self-contained page (inline CSS and JS, no external assets),
  semantic table with caption and column/row scopes, light/dark via
  `prefers-color-scheme`. A small inline script adds filters (status, source,
  domain, audience, reproduction level); without JavaScript the full table is
  shown and the filter bar stays hidden. A filter is only offered when the index
  carries that field: the current index has no `audience` values, so no audience
  filter is rendered yet.
- `index.md` - counts by status and domain with links to the pages below.
- `status-<slug>.md` and `domain-<slug>.md` - per-status and per-domain tables.
- Each row links to the card JSON and, when it exists, the sibling SVG preview.

No raw payloads are stored. Output is deterministic (sorted by
`registry_sequence`, no timestamps; the only date is the index `last_updated`).

```bash
uv run python scripts/claimbound_build_registry_view.py          # regenerate
uv run python scripts/claimbound_build_registry_view.py --check  # fail if stale
```

Generation first validates every index entry against its card JSON (the same
checks as `claimbound validate-all`) and aborts with a non-zero exit code on any
mismatch; cards are never edited. `--check` is also run by
`tests/test_registry_view.py`. Never edit the generated files by hand.

See [Static registry MVP acceptance criteria](STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md).
