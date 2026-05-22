# Track Family Ledgers

This directory is for R&D family ledgers created by `uv run claimbound new`.

A family ledger is not evidence. It is planning and preflight metadata for
related tracks: parent claim, non-overlap boundary, claim list, track modes,
proof-track budget, stop rules and closure decisions.

Validate a ledger before citing related tracks:

```bash
uv run claimbound validate-family docs/track_families/<ID>_FAMILY_LEDGER.json
```

or:

```bash
uv run python scripts/claimbound_validate_family_ledger.py \
  docs/track_families/<ID>_FAMILY_LEDGER.json
```

Validated evidence still lives in `docs/evidence_cards/`. The ledger prevents
diagnostic screening, repeated proof attempts or closed branches from being
misread as a completed evidence result.

Historical evidence cards created before this protocol do not need retroactive
ledgers. New ledgers are optional planning records and are validated only when a
`*_FAMILY_LEDGER.json` file exists.
