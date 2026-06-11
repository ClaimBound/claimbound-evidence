# ClaimBound Evidence

[![Stars: 1](docs/assets/badge_stars.svg)](https://github.com/ClaimBound/claimbound-evidence/stargazers)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](https://github.com/ClaimBound/claimbound-evidence/blob/main/LICENSE)
[![Python >=3.12](https://img.shields.io/badge/python-%3E%3D3.12-blue)](https://github.com/ClaimBound/claimbound-evidence/blob/main/pyproject.toml)
[![tests](https://github.com/ClaimBound/claimbound-evidence/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/ClaimBound/claimbound-evidence/actions/workflows/tests.yml)
[![Release: v0.3.2](docs/assets/badge_release.svg)](https://github.com/ClaimBound/claimbound-evidence/releases/tag/v0.3.2)

<p align="center">
  <img
    src="docs/assets/claimbound_logo.svg"
    alt="ClaimBound evidence logo"
    width="360"
  />
</p>

ClaimBound turns a narrow public AI, ML, data or software-development claim into
a small evidence card: a checkable record with the protocol, source boundary,
hashes, exact result status, claim boundary and reproduction level.

It is not a model leaderboard, hosted scoring service or certification
authority. It is an open-source toolkit for asking one plain question:

```text
Where is the evidence?
```

If there is no evidence card, the statement is still only a claim.

## Primary Public Workflows

ClaimBound is intentionally narrow. Start with these three foreground workflows:

| Workflow | Question it helps answer | Start here |
| --- | --- | --- |
| Public AI transparency | Did a public system-card or model-card **source boundary** pass a frozen audit? | [Current evidence tracks](docs/CURRENT_EVIDENCE_TRACKS.md) |
| European and public open data | Did an official public-data source pass a source-boundary or narrow empirical gate? | [EEA and NASA examples](docs/evidence_cards/README.md) |
| Software development evidence | Did a narrow build, validator or regression claim pass under fixed commands? | [Software development workflow](docs/SOFTWARE_DEVELOPMENT_WORKFLOW.md) |

Additional domains such as robotics, procurement, civic tech and education remain
documented as [future applications](docs/future_applications/README.md). Blocked
cards in those areas are first-class evidence, not hidden failures.

Artifact-only records (for example NYC TLC Phase 4 and CDC mirror summaries) are
listed separately in [docs/artifacts/README.md](docs/artifacts/README.md) and
are not presented as completed evidence cards.

<h2 id="claimbound-in-30-seconds">ClaimBound In 30 Seconds</h2>

ClaimBound turns a public statement like "we checked this", "this source
exists", "this benchmark reproduced", "this model is better" or "this risky
change passed" into a small evidence card: what exactly was checked, under
which frozen protocol, against which source, with which status, hashes,
limitations and reproduction level.

Its main job is anti-overclaiming. Green means one narrow claim passed under the
stated protocol, not "trust everything". Negative, blocked, insufficient and
drift results are first-class evidence too, because they stop weak or incomplete
claims from being silently upgraded into stronger ones.

Open the standalone document:
[docs/CLAIMBOUND_IN_30_SECONDS.md](docs/CLAIMBOUND_IN_30_SECONDS.md).

![ClaimBound workflow](docs/assets/claimbound_workflow.svg)

## For Reviewers And External Operators

Start here if you are reviewing the project, trying it from outside the
maintainer's machine, or checking what the open-source foreground is meant to
deliver:

- [Reviewer summary](docs/REVIEWER_SUMMARY.md) gives the problem, strongest
  cards, public-interest dimension and planned public deliverables in one page.
- [Public roadmap 2026](docs/ROADMAP_2026.md) maps the current public work
  package to concrete software, workflow and documentation outputs.
- [External operator starter pack](docs/EXTERNAL_OPERATOR_STARTER_PACK.md)
  explains how to read cards, request a card, rerun an existing card, report
  source drift or ask a boundary question.

## What A Card Shows

An evidence card keeps the useful claim small enough to inspect:

| Card field | Plain meaning |
| --- | --- |
| Claim | The exact public statement being checked. |
| Source | The public source or source documentation used for the check. |
| Protocol | The rules fixed before the result was accepted. |
| Status | Passed, negative, blocked, insufficient or reproduced. |
| Boundary | What the card proves and what it must not be used to claim. |
| Reproduction | Whether another run reproduced the outcome, and with what limits. |

Raw payloads, prompt text, transcripts and restricted source files stay outside
the public repository unless redistribution is clearly allowed. The public
record stores hashes, summaries and links so a local operator or organization
can keep private evidence reproducible without publishing sensitive material.

## Core Public Workflows

The evidence card is the public unit of work. Start with the smallest workflow
that keeps the claim honest.

| Workflow | Use it for | Read next |
| --- | --- | --- |
| Public AI documentation | Source-audit a public system-card, model-card or policy-document boundary without turning it into a runtime claim. | [Current evidence tracks](docs/CURRENT_EVIDENCE_TRACKS.md) |
| Public and European open data | Check source access, source drift, official pages and fair result boundaries for public datasets. | [Evidence card examples](docs/evidence_cards/README.md) |
| Reproduction and reruns | Rerun a completed card and report whether the narrow outcome, source bytes and limitations still match. | [External operator starter pack](docs/EXTERNAL_OPERATOR_STARTER_PACK.md) |
| Software and review evidence | Attach a bounded evidence record to a risky change, review gate, CI result or AI-assisted development workflow. | [Software development workflow](docs/SOFTWARE_DEVELOPMENT_WORKFLOW.md) |

Advanced protocol layers for related work families, frontier ledgers and tree
overlays are documented separately. Use the smallest layer stack that prevents
overclaiming; do not add layers to make a weak result look stronger.

## Example: AI System-Card Claim

Public claim:

```text
Anthropic publishes a public system-card index for its AI models.
```

ClaimBound narrows it:

```text
Can the official Anthropic system-card page be source-audited by URL, access
date, content type, expected markers and SHA-256 without making any model
safety, model quality or runtime-behavior claim?
```

Current card status:

```text
PASSED_UNDER_PROTOCOL / GREEN_VALIDATED
```

What this proves: the public source boundary passed the documented source-audit
gate at access time.

What it does not prove: that Claude or any Anthropic runtime is safer, better,
unchanged, deployment-ready or benchmark-superior.

[Read the JSON](docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json)
or open the
[visual SVG card](docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg).

## Example Cards

These are deliberately different outcomes: green means a narrow claim passed,
yellow means reproduction is useful but limited, amber means the source boundary
blocked a fair result, and red means the protocol ran but the claim did not
pass.

<p>
  <img
    src="docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg"
    alt="Green ClaimBound card for Anthropic system-card source audit"
    width="32%"
  />
  <img
    src="docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg"
    alt="Yellow ClaimBound card for NASA POWER reproduction with source-byte drift"
    width="32%"
  />
  <img
    src="docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg"
    alt="Red ClaimBound card for NOAA negative result"
    width="32%"
  />
</p>

| Example | Status | What the card proves | Links |
| --- | --- | --- | --- |
| Anthropic system-card source audit | `PASSED_UNDER_PROTOCOL` | The official system-card index passed a narrow public-document source audit. | [JSON](docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg) |
| EEA download-page source audit | `PASSED_UNDER_PROTOCOL` | The official EEA download page passed a narrow source-audit boundary before any larger data run was claimed. | [JSON](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg) |
| EEA AQ manual track | `BLOCKED_SOURCE` | The larger PM10 manual track could not fairly run from an incomplete public URL manifest. | [JSON](docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.json) / [SVG](docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.svg) |
| NASA POWER D-103 | `PASSED_UNDER_PROTOCOL` with `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | The frozen gate-level outcome reproduced, but fresh source bytes differed. | [JSON](docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json) / [SVG](docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg) |
| NOAA CO-OPS D-131 | `NEGATIVE_RESULT_UNDER_PROTOCOL` | The official-source run completed and honestly did not pass the frozen gate. | [JSON](docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json) / [SVG](docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg) |

For the full card list, see
[docs/evidence_cards/README.md](docs/evidence_cards/README.md). The registry
index is [docs/registry/evidence_index.json](docs/registry/evidence_index.json).

Start with [ClaimBound in 30 seconds](docs/CLAIMBOUND_IN_30_SECONDS.md), then
read [ClaimBound in 5 minutes](docs/CLAIMBOUND_IN_5_MINUTES.md) for the
plain-language version.

## Install

```bash
uv sync --extra dev
uv run --extra dev python -m pytest -n auto
```

## Quick Start

Create a draft scaffold:

```bash
uv run claimbound new
```

Create the same scaffold non-interactively:

```bash
uv run claimbound new \
  --source-url "https://example.org/source-docs" \
  --protocol-id "EXAMPLE_D001" \
  --domain "public-data" \
  --track-type "source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/EXAMPLE_D001"
```

Run local demo helpers:

```bash
uv run claimbound demo eea-source-audit
uv run claimbound demo grok-source-audit
uv run claimbound validate-all
```

`validate-all` checks committed evidence cards, the registry and any optional
`docs/track_families/*_FAMILY_LEDGER.json`, `docs/track_families/*_FRONTIER.json`
or `docs/track_families/*_TREE.json` files. Historical cards created before the
R&D family protocol do not need retroactive ledgers.

Prepare a local-only run root:

```bash
uv run claimbound run-root \
  --protocol-id EXAMPLE_D001 \
  --source-url https://example.org/source \
  --operator your-name-or-handle
```

`claimbound new` creates a request, protocol draft, playbook, checklist,
operator declaration, draft card, R&D family ledger and source-probe summary.
It is not evidence. Evidence begins only after an operator freezes the
protocol, runs the check, publishes a sanitized report, validates the card and
updates the registry.

## Next Steps: Simple To Technical

| Step | Document | Why read it |
| --- | --- | --- |
| 1 | [ClaimBound in 30 seconds](docs/CLAIMBOUND_IN_30_SECONDS.md) | The one-screen explanation. |
| 2 | [ClaimBound in 5 minutes](docs/CLAIMBOUND_IN_5_MINUTES.md) | The shortest plain-language walkthrough. |
| 3 | [Evidence card examples](docs/evidence_cards/README.md) | Green, yellow, red and blocked examples in one place. |
| 4 | [Getting started](docs/GETTING_STARTED.md) | Installation, local run roots and scaffold commands. |
| 5 | [Result status protocol v0.1](docs/RESULT_STATUS.md) | Exact statuses and the color semantics used by cards. |
| 6 | [Evidence card protocol v0.1](docs/EVIDENCE_CARD.md) | Required JSON fields and validation rules. |
| 7 | [Current evidence tracks](docs/CURRENT_EVIDENCE_TRACKS.md) | What the committed results prove and do not prove. |
| 8 | [Project next steps](docs/PROJECT_NEXT_STEPS.md) | What is next and what is intentionally out of scope. |

Individual pre-registration charters live in
[docs/protocols/](docs/protocols/). They are protocol-bound examples, not broad
claims.

## Deeper Guides

- [Manual audit protocol v0.1](docs/MANUAL_AUDIT_PROTOCOL.md)
- [AI operator protocol v0.1](docs/AI_OPERATOR_PROTOCOL.md) and
  [AI workflow](docs/AI_WORKFLOW.md)
- [No-AI EEA manual track](docs/manual_audit/EEA_AQ_D001_MANUAL_TRACK.md)
- [AI-assisted EEA track](docs/manual_audit/EEA_AQ_D001_AI_ASSISTED_TRACK.md)
- [EEA manual-track blocked card](docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.json)
- [Software development workflow](docs/SOFTWARE_DEVELOPMENT_WORKFLOW.md)
- [Audience and value](docs/AUDIENCE_AND_VALUE.md)
- [Audience workflows](docs/AUDIENCE_TESTIMONIAL_WORKFLOWS.md)
- [Protocol use by layer and audience](docs/PROTOCOL_USE_BY_LAYER_AND_AUDIENCE.md)
- [Protocol layers v2 and v3](docs/PROTOCOL_LAYERS_V2_V3.md)
- [Protocol v3 tree overlay](docs/PROTOCOL_V3_TREE_OVERLAY.md)
- [AI risk control with ClaimBound](docs/AI_RISK_CONTROL_WITH_CLAIMBOUND.md)
- [Demo tracks to evidence cards](docs/DEMO_TRACKS_TO_EVIDENCE_CARDS.md)

## Boundary

This repository is independently usable as an open evidence foreground. It
does not include, import or require private background technology.

This is a single-maintainer public repository. Evidence cards are reusable
examples and validation records, not a support queue, review service, legal
advice, or commitment that the maintainer will run third-party checks on demand.

For public review and sustainability boundaries, see
[governance](GOVERNANCE.md), [maintainer boundary](MAINTAINER_BOUNDARY.md) and
[release process](RELEASE_PROCESS.md).

The registry stores validated card metadata and sanitized report references, not
raw payloads. Distributed-ledger and chain timestamp features are outside the
current roadmap.

For the AI provenance log, use public PRs, commits, releases, checks, evidence
cards and registry entries first. GitHub organization audit logs are governance
support, not AI provenance by themselves. See
[AI provenance log and audit logs](docs/AI_PROVENANCE_LOG.md).

## Community

- [Contributing guide](CONTRIBUTING.md)
- [External operator starter pack](docs/EXTERNAL_OPERATOR_STARTER_PACK.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Discussions: maintainer announcements and community Q&A](https://github.com/ClaimBound/claimbound-evidence/discussions)

## License

Apache-2.0. See [LICENSE](LICENSE).
