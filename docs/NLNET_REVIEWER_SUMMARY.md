# ClaimBound Reviewer Summary

This page is a public orientation note for funding reviewers, first-time
readers and external operators. It is not a funding decision, endorsement or
private application document.

## What Problem ClaimBound Addresses

Public AI, ML, data and software claims often travel faster than their
evidence. A claim such as "we checked this", "this source exists", "this
benchmark reproduced" or "this model is better" is hard to inspect unless the
source, protocol, status and limitations are kept together.

ClaimBound turns one narrow public claim into a compact evidence card:

```text
public claim
  -> source boundary
  -> frozen protocol or checklist
  -> exact result status
  -> sanitized report and hashes
  -> claim boundary
  -> reproduction level
```

If there is no evidence card, the statement is still only a claim.

## What This Repository Already Contains

- Evidence-card JSON records and SVG previews rendered from JSON.
- A public registry index for validated cards.
- Validators for cards, registry entries and optional related-track ledgers.
- Public examples across green, yellow, amber and red outcomes.
- Manual and AI-assisted operator workflow docs.
- Source-audit protocols for public AI documentation and public-data sources.
- Rerun guidance for operators who want to reproduce an existing card.

Representative public examples:

| Example | Status | What it proves |
| --- | --- | --- |
| Anthropic system-card source audit | `PASSED_UNDER_PROTOCOL` | The official public source boundary passed a narrow source-audit gate. |
| EEA source audit | `PASSED_UNDER_PROTOCOL` | A European public-data source page exposed expected source-boundary markers. |
| NASA POWER D-103 | `PASSED_UNDER_PROTOCOL` with source-byte drift reproduction | A narrow public-data gate-level outcome reproduced with an explicit drift limitation. |
| NOAA CO-OPS D-131 | `NEGATIVE_RESULT_UNDER_PROTOCOL` | The official-source run completed and honestly did not pass the frozen gate. |
| EEA AQ manual track | `BLOCKED_SOURCE` | A larger manual track was blocked by an incomplete public source manifest. |

## 9-Month Public Work Package

The public foreground should stay narrow and concrete. A 9-month work package
should fund reusable open-source infrastructure, not a hosted service or private
background technology.

Planned public deliverables:

| Work area | Concrete deliverable | Acceptance signal |
| --- | --- | --- |
| Baseline consolidation | Status/card wording, link audits and release checks | `validate-all` passes and artifact-only records are not presented as cards. |
| SourceProbe v1 | Deterministic source metadata, hashes and source-boundary recommendations | Probe output supports public AI docs and public-data source audits, but cannot create a green card alone. |
| Scaffold hardening | Request, protocol, playbook, checklist, draft card and registry-patch scaffolds | Drafts remain gray and cannot become `PASSED_UNDER_PROTOCOL` automatically. |
| Operator workflows | Manual and AI-assisted runbooks, run roots, deviation logs and source-rights checks | A new operator can follow the workflow without hidden private steps. |
| Public AI claim protocol | Prompt/model/transcript/scoring metadata policy for public AI claims | Source audits never imply runtime behavior, safety or model superiority. |
| Static registry | Public read-only index and generated views | Every registry entry points to a validated card and no raw payload is stored. |
| Rerun workflow | Reproduction request path, rerun checklist and drift handling | Reruns can add evidence without changing the original claim. |

## Scope In

- Public-source AI documentation source audits.
- European and public open-data source-boundary checks.
- Narrow empirical public-data pass, negative, blocked and drift outcomes.
- Software/reproducibility evidence examples where commands, fixtures and
  limitations can be fixed before the result is accepted.
- Documentation, tests, validation commands, release process and accessibility
  improvements.

## Scope Out

- Model leaderboards.
- Runtime safety certification.
- Legal, compliance or procurement approval.
- Raw-data archival service.
- Hosted accounts, authenticated write API or operator reputation system.
- Blockchain, token, wallet or on-chain storage features.
- Market-signal products, forecasting services or private background
  technology.

## European Dimension

ClaimBound supports European digital commons by making public technology claims
more inspectable, reproducible and limitation-aware. The current public example
set includes a European Environment Agency source audit and an EEA Air Quality
manual-track blocked-source card. These examples are used only as public-data
source-boundary records; they do not claim EEA endorsement, legal reuse advice
or dataset completeness.

Useful European public-interest applications include:

- public-sector AI transparency;
- open-data stewardship;
- AI procurement evidence;
- open-science reproducibility;
- civic and public-interest source-boundary checks.

## Status Semantics

Positive, negative, blocked and drift outcomes are all useful evidence states.
ClaimBound is not optimized to produce only green cards. It is optimized to
prevent unsupported public claims from being silently upgraded into stronger
claims.

| Visual reading aid | Typical status | Meaning |
| --- | --- | --- |
| Green | `PASSED_UNDER_PROTOCOL` | One narrow claim passed under the written protocol. |
| Red | `NEGATIVE_RESULT_UNDER_PROTOCOL` | The protocol ran and the claim did not pass. |
| Amber | `BLOCKED_SOURCE` or `INSUFFICIENT_COVERAGE` | A fair empirical claim should not be made from the available source. |
| Yellow | `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | The outcome is useful but reproduction has an explicit limitation. |
| Gray | request or scaffold | Not evidence yet. |

## External Operator Path

External readers should start with
[External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md).

The lowest-risk contribution paths are:

- open an evidence request for one narrow public claim;
- request a rerun of an existing card;
- report source drift for a committed card;
- ask whether a card boundary is too broad or too narrow.

No issue, request or scaffold is evidence until a protocol is frozen, artifacts
are produced, the card validates and the registry entry is updated.
