# Independent Rerun Examples

This folder documents the **minimum local verification path** for external
operators. It is not reproduction evidence by itself.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) installed
- git

## Quick path

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run --extra dev python -m pytest -n auto
uv run claimbound validate-all
uv run claimbound demo eea-source-audit
uv run claimbound demo grok-source-audit
```

## Expected outputs

### pytest

- All tests pass (currently 48 tests).
- Exit code `0`.

### validate-all

Expected tail output shape:

```text
valid_cards=17
valid_registry=docs/registry/evidence_index.json
valid_family_ledgers=...
valid_frontier_ledgers=...
valid_tree_overlays=...
```

Card count may increase as new validated cards are added. The command must exit
`0` and report no validation errors.

### demo eea-source-audit

- Prints paths to the EEA source-audit card and related artifacts.
- Does not commit raw HTML payloads.

### demo grok-source-audit

- Prints paths to the Grok prompt source-audit example.
- Reinforces source-audit boundary, not runtime equivalence.

## What this does not prove

- Independent reproduction of a specific card by a second operator.
- Model safety, benchmark superiority or deployment readiness.
- That every blocked card should be reinterpreted as success.

For a full rerun workflow, read
[docs/INDEPENDENT_RERUN_WORKFLOW.md](../../docs/INDEPENDENT_RERUN_WORKFLOW.md)
and open a reproduction request issue when ready to publish a rerun card.
