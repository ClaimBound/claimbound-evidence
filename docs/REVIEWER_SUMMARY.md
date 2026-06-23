# ClaimBound Reviewer Summary

This page is a public orientation note for first-time readers, reviewers and
external operators. It is not an endorsement, selection note, legal opinion or
private project document.

## What Problem ClaimBound Addresses

Public AI, ML, data and software claims often travel faster than their evidence.
A claim such as "we checked this", "this source exists", "this benchmark
reproduced" or "this model is better" is hard to inspect unless the source,
protocol, status and limitations are kept together.

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

## Current Baseline Versus Planned Work

The public repository already contains a working open-source baseline. A separate
public work package (described in [Public roadmap 2026](ROADMAP_2026.md)) is
planned to harden that baseline into additional reusable infrastructure.

| Already public now | Planned next (not claimed as completed here) |
| --- | --- |
| Evidence-card JSON/SVG, registry index, validators, 86 tests | SourceProbe v1 implementation |
| Cross-platform CLI (`doctor`, `inspect`, `rerun`, `drift`, `verify`) on Windows/macOS/Linux | Static registry generated views |
| EU and public AI source-audit runners for existing card types | Scaffold workflow hardening |
| Scaffold drafts via `claimbound new` | Operator workflow hardening and external adoption |
| Manual and AI-assisted workflow docs; CI on ubuntu + windows | Independent external reruns (`INDEPENDENT_RERUN`, `MULTI_OPERATOR`) |
| Rerun workflow docs, issue templates, maintainer rerun cards; 33 honest cards | Expanded tutorial set and accessibility pass |

Documents such as [SourceProbe v1 acceptance criteria](SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md)
and [Static registry MVP acceptance criteria](STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md)
are **pre-implementation specifications**, not completed deliverables. See
[Planned work not shipped](PLANNED_NOT_SHIPPED.md).

Start with the one-page [Reviewer path](REVIEWER_PATH.md). External operators can
close **open** VERIFY mirrors #85–#87 using split packs in
[External verification](external_verification/README.md). See
[Common misreadings](COMMON_MISREADINGS.md) before interpreting card colors.

## Not A Duplicate Of

ClaimBound is intentionally narrow. It complements adjacent projects instead of
replacing them.

| Adjacent project | What it already does | ClaimBound boundary |
| --- | --- | --- |
| OSF / preregistration platforms | Register study plans before outcomes are known | Publish **outcome evidence cards** with exact status, hashes, claim boundary and forbidden inferences |
| OpenML / MLCommons-style benchmarks | Broad model evaluation and leaderboard tables | Small frozen protocols and source-boundary checks; no global ranking by default |
| Fact-checking / newsroom workflows | Editorial verification of public statements | Machine-checkable evidence records tied to frozen protocols and public sources |
| EviBound (research-agent execution gates) | Dual-gate agent execution with MLflow artifacts | Public evidence cards for narrow claims on public sources — see [Related work](RELATED_WORK_AND_INDEPENDENCE.md) |

Key sentence:

```text
OSF registers the plan; ClaimBound publishes the outcome card with exact status
and forbidden claims.
```

## What This Repository Already Contains

- Evidence-card JSON records and SVG previews rendered from JSON.
- A public registry index for validated cards.
- Validators for cards, registry entries and optional related-track ledgers.
- Public examples across green gate passes, amber blocked sources, red negative
  gates and yellow reproduction chips for source-byte drift.
- Manual and AI-assisted operator workflow docs.
- Source-audit protocols for public AI documentation and public-data sources.
- Rerun guidance for operators who want to reproduce an existing card.

Representative public examples:

| Example | Status | What it proves |
| --- | --- | --- |
| Anthropic system-card source audit | `PASSED_UNDER_PROTOCOL` | The official public source boundary passed a narrow source-audit gate. |
| EEA source audit | `PASSED_UNDER_PROTOCOL` | A European public-data source page exposed expected source-boundary markers. |
| EU Data Portal source audit | `PASSED_UNDER_PROTOCOL` | The European Data Portal landing page passed a narrow source-boundary audit. |
| EEA content reuse FAQ source audit | `PASSED_UNDER_PROTOCOL` | The EEA reuse FAQ page passed a narrow reachability and navigation-link audit. |
| Eurostat API guidelines source audit | `PASSED_UNDER_PROTOCOL` | The Eurostat API guidelines page passed a narrow copyright and documentation-link audit. |
| NASA POWER D-103 | `PASSED_UNDER_PROTOCOL` with source-byte drift reproduction | A narrow public-data gate-level outcome reproduced with drift in `reproduction_level`. |
| NASA / NOAA maintainer reruns | Baseline cards plus `reproduction_attempt` siblings | Maintainer `SINGLE_OPERATOR_RERUN` only; not `INDEPENDENT_RERUN` or `MULTI_OPERATOR`. |
| NOAA CO-OPS D-131 | `NEGATIVE_RESULT_UNDER_PROTOCOL` | The official-source run completed and honestly did not pass the frozen gate. |
| API parity registry gate | `PASSED_UNDER_PROTOCOL` | Frozen registry validators exited 0; registry metadata parity only. |
| EEA AQ manual track | `BLOCKED_SOURCE` | A larger manual track was blocked by an incomplete public source manifest. |

## European Dimension

ClaimBound includes European public-data examples such as the EEA source-audit,
EU Data Portal, EEA reuse FAQ and Eurostat source-audit cards, plus the blocked
EEA AQ manual-track card. See [European Dimension](EUROPEAN_DIMENSION.md) for
the public-interest framing, SVG previews, operator rerun commands and explicit
limits.

## Planned Public Work Package

The public foreground should stay narrow and concrete. The [roadmap](ROADMAP_2026.md)
describes planned hardening work. Acceptance-criteria documents for some items
exist as specs only; implementation is part of that planned package, not claimed
as already completed in this repository.

Planned public deliverables:

| Work area | Concrete deliverable | Acceptance signal |
| --- | --- | --- |
| Baseline consolidation | Status/card wording, link audits and release checks | `validate-all` passes and artifact-only records are not presented as cards. |
| SourceProbe v1 | Deterministic source metadata, hashes and source-boundary recommendations | Probe output supports public AI docs and public-data source audits, but cannot create a green card alone. |
| Scaffold hardening | Request, protocol, playbook, checklist, draft card and registry-patch scaffolds | Drafts remain gray and cannot become `PASSED_UNDER_PROTOCOL` automatically. |
| Operator workflows | Manual and AI-assisted runbooks, run roots, deviation logs and source-rights checks | A new operator can follow the workflow without hidden private steps. |
| Public AI claim protocol | Public-source rules, model/API metadata fields, prompt/transcript hash policy and screenshot-only limits | Source audits never imply runtime behavior, safety or model superiority. |
| Static registry | Public read-only index and generated views | Every registry entry points to a validated card and no raw payload is stored. |
| Rerun workflow | Reproduction request path, rerun checklist, drift handling and external adoption | Docs, templates and maintainer examples exist; independent external reruns remain the acceptance signal. |

## Scope In

- Public-source AI documentation source audits.
- European and public open-data source-boundary checks.
- Narrow empirical public-data pass, negative, blocked and drift outcomes.
- Software and reproducibility evidence examples where commands, fixtures and
  limitations can be fixed before the result is accepted.
- Documentation, tests, validation commands, release process and accessibility
  improvements.

## Scope Out

- Model leaderboards.
- Runtime safety certification.
- Legal, compliance or procurement approval.
- Raw-data archival service.
- Hosted accounts, authenticated write API or operator reputation system.
- Broad platform features outside evidence-card validation, registry and
  operator workflow needs.
- Unrelated private systems or private performance claims.

## European Public-Interest Dimension

ClaimBound supports digital commons by making public technology claims more
inspectable, reproducible and limitation-aware. The current public example set
includes a European Environment Agency source audit and an EEA Air Quality
manual-track blocked-source card. These examples are used only as public-data
source-boundary records; they do not claim EEA endorsement, legal reuse advice
or dataset completeness.

Useful public-interest applications include:

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
| Yellow (reproduction chip) | `reproduction_level: REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | The gate outcome is useful but reproduction has an explicit source-byte limitation. |
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
