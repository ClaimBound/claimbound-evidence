# Common Misreadings

ClaimBound is designed to prevent silent overclaiming. These mistakes appear
often in first reviews. This page is a public FAQ, not legal advice.

## Green card does not mean "safe" or "good"

| Misreading | Correct reading |
| --- | --- |
| "The model is safe." | A **narrow** claim passed under a **frozen** protocol on one source boundary. |
| "The product is ready to deploy." | Source-audit cards check URLs, markers and hashes — not runtime behavior. |
| "This benchmark proves superiority." | ClaimBound is not a leaderboard; it records one bounded outcome. |

## Yellow reproduction chip is not a failed gate

`reproduction_level` can record source-byte drift while `result_status` stays
`PASSED_UNDER_PROTOCOL`. Example: [NASA POWER D-103](evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json).

Drift is explicit evidence, not a hidden downgrade.

## Red and blocked cards are success for the project

| Status | Meaning |
| --- | --- |
| `NEGATIVE_RESULT_UNDER_PROTOCOL` | The protocol ran; the narrow claim did not pass. |
| `BLOCKED_SOURCE` | A fair empirical claim should not be made from the available source. |

A repository that shows only green cards is **less** credible for ClaimBound's
purpose.

## Source audit is not dataset verification

EEA, EU ODP, Eurostat and public AI documentation cards check **source
boundaries** — reachability, expected links, content type, hashes. They do **not**
prove:

- full dataset coverage,
- legal redistribution rights for all data,
- pollutant-model correctness,
- model safety or benchmark ranking.

See [European Dimension](EUROPEAN_DIMENSION.md) limits section.

## VERIFY issue closure by maintainer is bootstrap only

VERIFY mirrors #85–#92 may show maintainer bootstrap comments. That proves the
workflow exists; it does **not** replace independent external reruns. See
[External verification packs](external_verification/README.md).

## Roadmap rows are not shipped features

Documents such as [SourceProbe v1 acceptance criteria](SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md)
and [Static registry MVP acceptance criteria](STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md)
are **pre-implementation specifications**. See
[Planned work not shipped](PLANNED_NOT_SHIPPED.md).

## PROGRAM_FIT_D001 is not program approval

[PROGRAM_FIT_D001](evidence_cards/CLAIMBOUND-PROGRAM_FIT_D001-2026-06-04.json) is an
**advanced optional** methodology demo: a narrow public-materials self-check. It
does not prove endorsement, award likelihood or reviewer acceptance.

## Demos and scaffolds are not evidence

`claimbound demo`, `claimbound new` and gray scaffold files are operator aids.
Evidence starts only after protocol freeze, sanitized artifacts, validator pass
and registry update.

## Artifact-only records are not missing cards by accident

NYC TLC Phase 4 and CDC mirror summaries live in the
[artifacts catalog](artifacts/README.md). They are intentionally outside the 40-card
registry until promotion criteria are met.
