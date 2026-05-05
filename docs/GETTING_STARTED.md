# Getting Started With ClaimBound

ClaimBound is easiest to understand as a small evidence pipeline for one narrow
claim.

```text
official source
  -> frozen protocol
  -> local payload handling outside this repository
  -> runner or manual checklist
  -> exact result status
  -> evidence card
  -> public registry entry
```

## The Core Rule

Write the rules before looking at the outcome.

A good ClaimBound result says:

```text
Under protocol P, using official source S, candidate C received status R under
frozen gate G.
```

A bad ClaimBound result says:

```text
This model works generally.
This system is ready for deployment.
This method is better than all other methods.
```

## Minimal Workflow

1. Pick a narrow claim.
2. Confirm the official public source and source boundary.
3. Record rights, attribution and payload-handling notes.
4. Freeze the protocol, target, baselines, controls and acceptance gate.
5. Run the track or complete the checklist.
6. Publish the exact status, including negative, blocked or insufficient
   coverage outcomes.
7. Create a compact evidence card.
8. Add the card to the public registry only after validation.

## Valid Result Statuses

Use the documented status values:

- `PASSED_UNDER_PROTOCOL`
- `NEGATIVE_RESULT_UNDER_PROTOCOL`
- `BLOCKED_SOURCE`
- `INSUFFICIENT_COVERAGE`
- `REPRODUCED_OUTCOME`
- `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`

Negative and blocked outcomes are useful. They prevent selective reporting and
make source limits visible.

## Minimal Local Check

```bash
uv sync --extra dev
uv run --extra dev python -m pytest -n auto
uv run --extra dev python scripts/claimbound_validate_evidence_card.py \
  docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json
```

## Read Next

- [Audience and value](AUDIENCE_AND_VALUE.md)
- [Current evidence tracks](CURRENT_EVIDENCE_TRACKS.md)
- [Evidence card specification](EVIDENCE_CARD.md)
- [Manual audit protocol](MANUAL_AUDIT_PROTOCOL.md)
- [AI operator protocol](AI_OPERATOR_PROTOCOL.md)
