# API_PARITY_D001 Pre-Registration Charter

Status: frozen software-development evidence protocol for registry parity check.

Created: 2026-06-15

## Claim Boundary

Under frozen `API_PARITY_D001`, registry validation exits 0 and reports the
expected `registry_name` and `card_count` for the committed evidence index.

It must not claim production readiness, security certification, total validator
correctness or universal API stability.

## Source

- Source name: ClaimBound evidence repository
- Source URL: https://github.com/ClaimBound/claimbound-evidence
- Domain: software-development
- Execution mode: MANUAL_NO_AI

## Frozen Pass Gate

The gate passes only when all of these are true on the access date:

- `uv run python scripts/claimbound_validate_registry.py` exits 0;
- `uv run claimbound validate-all` exits 0;
- `registry_name` and `card_count` in `docs/registry/evidence_index.json` match
  the frozen expectation recorded in the sanitized summary;
- no registry statistics or gate thresholds were changed after the run.

## Forbidden Claims

Do not claim:

- production deployment readiness;
- security certification;
- complete validator coverage;
- external API correctness beyond committed registry metadata.
