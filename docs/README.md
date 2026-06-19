# ClaimBound Documentation Index

Use this page to choose a reading path. You do not need every protocol file to
try ClaimBound.

## Reviewer Path

For first-time readers, program reviewers, journalists and external inspectors:

1. [ClaimBound in 30 seconds](CLAIMBOUND_IN_30_SECONDS.md)
2. [Reviewer summary](REVIEWER_SUMMARY.md) — problem, baseline vs planned work,
   differentiation from adjacent projects
3. [European Dimension](EUROPEAN_DIMENSION.md)
4. [Evidence card examples](evidence_cards/README.md)
5. [Public roadmap 2026](ROADMAP_2026.md)

Quick validation:

```bash
uv sync --extra dev
uv run claimbound validate-all
```

## Operator Path

For people who want to run or challenge a card locally:

1. [ClaimBound in 5 minutes](CLAIMBOUND_IN_5_MINUTES.md)
2. [Getting started](GETTING_STARTED.md)
3. [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md)
4. [Result status protocol](RESULT_STATUS.md)
5. [Evidence card protocol](EVIDENCE_CARD.md)
6. [Independent rerun workflow](INDEPENDENT_RERUN_WORKFLOW.md)

## Developer Path

For contributors extending validators, runners or card tooling:

1. [Contributing guide](../CONTRIBUTING.md)
2. [Evidence card protocol](EVIDENCE_CARD.md)
3. [Manual audit protocol](MANUAL_AUDIT_PROTOCOL.md)
4. [AI operator protocol](AI_OPERATOR_PROTOCOL.md)
5. [Software development workflow](SOFTWARE_DEVELOPMENT_WORKFLOW.md)

## Advanced (Optional)

These layers help manage related tracks and complex R&D families. They are
**not required** to read cards, run demos or validate the registry.

- [Protocol layers v2 and v3](PROTOCOL_LAYERS_V2_V3.md)
- [Protocol v3 tree overlay](PROTOCOL_V3_TREE_OVERLAY.md)
- [R&D family protocol](R_AND_D_FAMILY_PROTOCOL.md)
- [Track families](track_families/README.md)
- [12 AI Life Rules](TWELVE_AI_LIFE_CONTROLS.md)
- [Future applications](future_applications/README.md)

## Examples (Not First-Screen Evidence)

Optional methodology patterns kept out of the main card table:

- [Program eligibility self-check](examples/PROGRAM_ELIGIBILITY_SELF_CHECK.md) —
  applicant-side example only; not program approval or endorsement evidence

## Pre-Implementation Specs

Acceptance criteria for planned infrastructure. These are design documents, not
completed implementations:

- [SourceProbe v1 acceptance criteria](SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md)
- [Static registry MVP acceptance criteria](STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md)