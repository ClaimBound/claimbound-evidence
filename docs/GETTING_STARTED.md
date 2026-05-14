# Getting Started With ClaimBound

ClaimBound is easiest to understand as a small evidence pipeline for one narrow
claim.

If there is no evidence card, the statement is still only a claim.

![ClaimBound workflow](assets/claimbound_workflow.svg)

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
uv run claimbound validate-all
uv run --extra dev python scripts/claimbound_validate_evidence_card.py \
  docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json
```

## Common Commands

| Command | What it does |
| --- | --- |
| `uv run claimbound new` | Creates a draft request, protocol, playbook, checklist, operator declaration, draft card and source-probe summary. Prompts interactively in a terminal. |
| `uv run claimbound new-track` | Alias for `new`; kept for people who think in "track" language. |
| `uv run claimbound run-root --protocol-id ... --source-url ...` | Creates a local-only run directory under `$HOME/claimbound_runs/` with `raw/`, `logs/`, `hashes/`, `reports/` and `transcripts/`. |
| `uv run claimbound demo eea-source-audit` | Runs the EEA source-audit demo helper and writes a sanitized report under the demo run root. |
| `uv run claimbound demo grok-source-audit` | Clones or reuses the public `xai-org/grok-prompts` repository in a local-only demo root, then writes source-audit metadata and hashes. |
| `uv run claimbound validate-all` | Validates all committed evidence cards and the registry index. |

These commands are useful for private local work too. A person or organization
can keep raw payloads, prompt text, transcripts and logs inside a local run
root, while publishing only the sanitized hashes and evidence card.

## Create A New Scaffold

Interactive:

```bash
uv run claimbound new
```

Non-interactive:

```bash
uv run claimbound new \
  --source-url "https://example.org/source-docs" \
  --protocol-id "EXAMPLE_D001" \
  --domain "public-data" \
  --track-type "source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/EXAMPLE_D001"
```

The scaffold is not evidence. It creates a request, protocol draft, playbook,
checklist, operator declaration, draft card and source-probe summary so an
operator can freeze the real protocol and run the track without missing common
steps.

## Prepare A Local Run Root

Manual and AI-assisted runs should keep raw payloads outside this repository:

```bash
uv run claimbound run-root \
  --protocol-id "EXAMPLE_D001" \
  --source-url "https://example.org/source-docs" \
  --operator "your-name-or-handle"
```

This creates a local-only directory under `$HOME/claimbound_runs/` with standard
`raw/`, `logs/`, `hashes/`, `reports/` and `transcripts/` folders, plus
`RUN_CONTEXT.md`, `DEVIATIONS.md` and `LOCAL_MANIFEST.md`.

## Read Next

- [ClaimBound in 5 minutes](CLAIMBOUND_IN_5_MINUTES.md)
- [Audience and value](AUDIENCE_AND_VALUE.md)
- [Current evidence tracks](CURRENT_EVIDENCE_TRACKS.md)
- [Evidence card specification](EVIDENCE_CARD.md)
- [Manual audit protocol](MANUAL_AUDIT_PROTOCOL.md)
- [AI operator protocol](AI_OPERATOR_PROTOCOL.md)
- [AI workflow](AI_WORKFLOW.md)
