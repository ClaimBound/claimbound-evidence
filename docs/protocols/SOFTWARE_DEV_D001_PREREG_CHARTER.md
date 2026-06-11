# SOFTWARE_DEV_D001 Pre-Registration Charter

Status: frozen software-development evidence protocol for validator gate check.

Created: 2026-06-11

## Claim Boundary

This track checks only a narrow `validator_regression_gate` claim for the
ClaimBound evidence-card validator: whether a card JSON missing the required
field `execution_mode` is rejected by the frozen validation command.

It must not claim general software security, full test-suite adequacy, CI
replacement, code-review sufficiency or repository-wide quality.

## Source

- Source name: ClaimBound evidence repository (validator and tests)
- Source URL: https://github.com/ClaimBound/claimbound-evidence
- Domain: software-development
- Audience: Software developers and maintainers
- Execution mode: MANUAL_NO_AI

## Frozen Pass Gate

The gate passes only when all of these are true on the access date:

- `uv run --extra dev python -m pytest tests/test_evidence_card.py::test_evidence_card_requires_execution_mode -q` exits 0;
- the test observes violation text `missing required field: execution_mode`;
- `uv run claimbound validate-all` exits 0 on the committed registry;
- no validator thresholds or required-field list were changed after the run.

## Stop Conditions

Stop and record blocked or insufficient status if the test file, validator or
required-field contract changes before the card is frozen.
