## I Reproduced This Card

Use this PR template for an independent rerun or reproduction attempt of an
existing ClaimBound evidence card.

## Card Reproduced

- Evidence card:
- Original protocol:
- Original result status:
- Original sanitized report:

## Rerun Boundary

- Operator name or handle:
- Execution mode: `MANUAL_NO_AI` / `AUTOMATED_AI_ASSISTED`
- Run date:
- Source access date:
- Source URL or API endpoint:
- Local run root outside this repository:

## What I Reproduced

Choose one:

- [ ] Same result status.
- [ ] Same gate-level outcome, but source bytes drifted.
- [ ] Negative result under the original protocol.
- [ ] Blocked source.
- [ ] Insufficient coverage.
- [ ] Could not complete; see deviations.

## Required Artifacts

- [ ] Raw payloads, transcripts and restricted materials were kept outside this repository.
- [ ] Local-only raw artifact hashes or a blocked-hashing reason are recorded.
- [ ] A sanitized summary JSON is committed under `artifacts/`.
- [ ] A reproduction evidence card JSON is committed under `docs/evidence_cards/`.
- [ ] SVG was rendered from the validated JSON card when applicable.
- [ ] Registry entry was updated only after validation.

## Deviations

List every deviation from the original protocol, including source-byte drift,
API changes, unavailable files, changed timestamps, changed metadata, missing
hashes or manual judgment that became necessary.

## Verification

- [ ] `uv run claimbound validate-all` passes.
- [ ] `uv run --extra dev python -m pytest -q` passes.
- [ ] The PR does not claim model superiority, deployment readiness,
      certification or correctness outside the reproduced protocol.
