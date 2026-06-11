# Robotics And Mobility (Future Application)

ClaimBound can support **evidence around release engineering** for robotics,
autonomous systems and mobility software. It is not a millisecond-level safety
controller and does not certify vehicles or robots.

## Suitable narrow claims

- A frozen scenario manifest was source-audited before a release gate.
- A public documentation or dataset boundary passed a source-audit protocol.
- A regression or parity gate passed under fixed commands and fixtures.

## Unsuitable broad claims

- The robot, vehicle or model is generally safe.
- Runtime behavior matches a public document without an explicit equivalence protocol.
- ISO, IEC, automotive or robotics safety processes are replaced.

## Current public examples

| Record | Type | Status |
| --- | --- | --- |
| [Civic claim D001](../evidence_cards/CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json) | Validated card | `BLOCKED_SOURCE` |
| [NYC TLC Phase 4](../evidence/NYC_TLC_PHASE4_NEGATIVE_RESULT.md) | Artifact-only | Negative run |

The civic card shows blocked-source discipline for mobility-related public data.
The NYC TLC artifact shows a negative empirical run that was not promoted to a
completed card.

## Read next

- [AI risk control with ClaimBound](../AI_RISK_CONTROL_WITH_CLAIMBOUND.md)
- [Protocol use by layer and audience](../PROTOCOL_USE_BY_LAYER_AND_AUDIENCE.md)
