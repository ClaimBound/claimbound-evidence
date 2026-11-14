# Quick start

Validate one card, look at its result and see what it does not claim.

```bash
pipx install protocolith
curl -LO https://raw.githubusercontent.com/protocolith/protocolith/main/docs/evidence_cards/PLITH-NASA-POWER-D103-2026-04-29.json
protocolith validate-card PLITH-NASA-POWER-D103-2026-04-29.json
protocolith inspect card PLITH-NASA-POWER-D103-2026-04-29.json
```

`validate-card` checks the card against the protocol rules: required fields, exact status and
level strings, `raw_payload_committed` set to `false`, a baseline summary for positive records,
a block or drift reason where applicable, and consistent AI-assistance fields. It does not
judge whether the claim is true. `inspect card` prints a short summary; add
`--keys claim_boundary known_limitations` to read specific fields.

Before quoting a card, read three fields: `result_status`, `reproduction_level` and
`claim_boundary`. The [concepts](concepts.md) page explains them.

## Next

- Run the whole registry check from a clone: `uv run protocolith validate-all`.
- Repeat a card yourself: [independent rerun workflow](INDEPENDENT_RERUN_WORKFLOW.md).
- Every command and option: [command reference](CLI.md).
