# Evidence Request: QWC_API_SERVER_D001

Status: request scaffold. This is not evidence.

## Public Claim

To be written narrowly by the requester before protocol freeze.

## Narrow ClaimBound Question

Can a QWC_API_SERVER development track produce a protocol-bound evidence record for one narrow local API behavior check, using sanitized command logs, fixture hashes and a boundary that does not claim deployment readiness or correctness outside the protocol?

## Main Audience

Software developers, maintainers and AI-assisted development operators.

## Preferred Track

AUTOMATED_AI_ASSISTED or MANUAL_NO_AI, depending on who executes the local run.

## Proposed Sources

- Local or private QWC_API_SERVER source boundary, recorded by repository note and commit hash.
- Local fixture manifest or golden-vector manifest.
- Sanitized command logs and report hashes.

## Proposed Decision Rule

Not recorded yet. Must be fixed before execution.

## Known Reproducibility Risks

- local environment may differ across operators;
- private source may not be redistributable;
- fixture data may need a sanitized manifest instead of raw payload publication;
- API behavior may depend on configuration that must be recorded without exposing private material.

## Claims This Card Must Not Make

- no production-readiness claim;
- no broad project-correctness claim;
- no certification claim;
- no claim about behavior outside the frozen endpoint, fixture set, runner and environment;
- no claim that ordinary software tests or review are replaced.
