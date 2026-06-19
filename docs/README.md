# ClaimBound Documentation Index

Use this page to choose a reading path. You do not need every protocol file to
try ClaimBound.

## Reviewer Path

For first-time readers, program reviewers, journalists and external inspectors:

1. [Reviewer path (one page)](REVIEWER_PATH.md) — fastest honest baseline
2. [ClaimBound in 30 seconds](CLAIMBOUND_IN_30_SECONDS.md)
3. [Reviewer summary](REVIEWER_SUMMARY.md) — problem, baseline vs planned work,
   differentiation from adjacent projects
4. [Common misreadings](COMMON_MISREADINGS.md)
5. [Current evidence tracks](CURRENT_EVIDENCE_TRACKS.md) — plain-language map of
   all registry cards
6. [Evidence card examples](evidence_cards/README.md)
7. [Case studies](case_studies/README.md)
8. [Planned work not shipped](PLANNED_NOT_SHIPPED.md) — roadmap vs current code
9. [Artifacts catalog](artifacts/README.md) — NYC TLC / CDC artifact-only records
10. [Public roadmap 2026](ROADMAP_2026.md)
11. [European Dimension](EUROPEAN_DIMENSION.md)

Closing VERIFY mirrors? See [External verification packs](external_verification/README.md).
Issues **#85–#87** are open for **independent** external operators.

Quick validation:

```bash
uv sync --extra dev
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

## Operator Path

For people who want to run or challenge a card locally:

1. [Start without coding](START_WITHOUT_CODING.md) — Windows/macOS/Linux, no jq or bash
2. [Platform support](PLATFORM_SUPPORT.md)
3. [ClaimBound in 5 minutes](CLAIMBOUND_IN_5_MINUTES.md)
4. [Getting started](GETTING_STARTED.md)
5. [External verification packs](external_verification/README.md) — split VERIFY work
6. [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md)
7. [Result status protocol](RESULT_STATUS.md)
8. [Evidence card protocol](EVIDENCE_CARD.md)
9. [Independent rerun workflow](INDEPENDENT_RERUN_WORKFLOW.md)
10. [Artifacts catalog](artifacts/README.md) — not registry cards

Rerun playbooks: [runbooks/](runbooks/README.md).

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
completed implementations. See [Planned work not shipped](PLANNED_NOT_SHIPPED.md).

- [SourceProbe v1 acceptance criteria](SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md)
- [Static registry MVP acceptance criteria](STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md)

## Deep Dives (Optional, Not First-Screen)

These pages support specific audiences or future direction. They are not part of
the default reviewer or operator path.

| Document | Role |
| --- | --- |
| [Project next steps](PROJECT_NEXT_STEPS.md) | Maintainer focus notes |
| [Global evidence registry direction](GLOBAL_EVIDENCE_REGISTRY.md) | Future hosted-registry vision only |
| [Reproduction guide (legacy)](REPRODUCTION.md) | NASA/NOAA background; use rerun workflow + tier C packs |
| [Flagship Grok workflow](FLAGSHIP_WORKFLOW_GROK_EVIDENCE.md) | Worked public-AI example |
| [Audience and value](AUDIENCE_AND_VALUE.md) | Audience-specific positioning |
| [Claims](CLAIMS.md) | Claim-boundary language reference |