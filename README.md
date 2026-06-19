# ClaimBound Evidence

[![GitHub stars](https://img.shields.io/github/stars/ClaimBound/claimbound-evidence?style=flat&logo=github)](https://github.com/ClaimBound/claimbound-evidence/stargazers)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](https://github.com/ClaimBound/claimbound-evidence/blob/main/LICENSE)
[![Python >=3.12](https://img.shields.io/badge/python-%3E%3D3.12-blue)](https://github.com/ClaimBound/claimbound-evidence/blob/main/pyproject.toml)
[![tests](https://img.shields.io/github/actions/workflow/status/ClaimBound/claimbound-evidence/tests.yml?branch=main&label=tests)](https://github.com/ClaimBound/claimbound-evidence/actions/workflows/tests.yml)
[![release](https://img.shields.io/github/v/release/ClaimBound/claimbound-evidence?label=release)](https://github.com/ClaimBound/claimbound-evidence/releases/latest)
[![evidence cards](https://img.shields.io/badge/evidence_cards-24-blue)](docs/registry/evidence_index.json)

<p align="center">
  <img
    src="docs/assets/claimbound_logo.svg"
    alt="ClaimBound evidence logo"
    width="360"
  />
</p>

ClaimBound turns a narrow public AI, ML, data or software-development claim into
a small evidence card: protocol, source boundary, hashes, exact result status,
claim boundary and reproduction level.

It is not a model leaderboard, hosted scoring service or certification authority.
It is an open-source toolkit for asking one plain question:

```text
Where is the evidence?
```

If there is no evidence card, the statement is still only a claim. Green means
one narrow claim passed under a frozen protocol — not "trust everything".
Negative, blocked and drift outcomes are first-class evidence too.

Read the one-screen walkthrough in [ClaimBound in 30 seconds](docs/CLAIMBOUND_IN_30_SECONDS.md)
or the [documentation index](docs/README.md) for reviewer, operator and advanced paths.

![ClaimBound workflow](docs/assets/claimbound_workflow.svg)

## Public Workflows

| Workflow | Question it helps answer | Start here |
| --- | --- | --- |
| Public AI transparency | Did a public system-card or model-card **source boundary** pass a frozen audit? | [Current evidence tracks](docs/CURRENT_EVIDENCE_TRACKS.md) |
| European and public open data | Did an official public-data source pass a source-boundary or narrow empirical gate? | [Evidence card examples](docs/evidence_cards/README.md) |
| Software development evidence | Did a narrow build, validator or regression claim pass under fixed commands? | [Software development workflow](docs/SOFTWARE_DEVELOPMENT_WORKFLOW.md) |

Blocked cards, artifact-only records and optional advanced protocol layers are
documented separately. They are not hidden failures. See
[future applications](docs/future_applications/README.md),
[artifacts catalog](docs/artifacts/README.md) and
[advanced optional docs](docs/README.md#advanced-optional).

## Example Cards

Each SVG uses separate chips. **Green** and **red** on the result-status chip
mean a narrow gate pass or honest non-pass. **Yellow** appears on the
**reproduction** chip when `reproduction_level` records source-byte drift — not
on the gate outcome itself. None of this implies general model quality.

<p>
  <img
    src="docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg"
    alt="Green ClaimBound card for Anthropic system-card source audit"
    width="32%"
  />
  <img
    src="docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg"
    alt="ClaimBound card with green gate pass and yellow reproduction chip for NASA POWER source-byte drift"
    width="32%"
  />
  <img
    src="docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg"
    alt="Red ClaimBound card for NOAA negative result"
    width="32%"
  />
</p>

More examples, including EU source audits and blocked-source cards:
[evidence cards](docs/evidence_cards/README.md) ·
[registry index](docs/registry/evidence_index.json)

## For Reviewers And External Operators

- [Reviewer summary](docs/REVIEWER_SUMMARY.md) — problem, strongest cards, baseline
  versus roadmap, differentiation from adjacent projects
- [European Dimension](docs/EUROPEAN_DIMENSION.md) — EU open-data angle and limits
- [External verification packs](docs/external_verification/README.md) — split VERIFY
  work across Tier A/B/C operators
- [External operator starter pack](docs/EXTERNAL_OPERATOR_STARTER_PACK.md) — read,
  rerun, drift report or boundary question paths
- [Planned work not shipped](docs/PLANNED_NOT_SHIPPED.md) — roadmap vs current code
- [Artifacts catalog](docs/artifacts/README.md) — NYC TLC / CDC artifact-only records
- [Public roadmap 2026](docs/ROADMAP_2026.md) — planned open-source hardening work

Independent from [EviBound](https://arxiv.org/abs/2511.05524); see
[scope split](docs/RELATED_WORK_AND_INDEPENDENCE.md).

## Install

Works on Windows, macOS and Linux. See [platform support](docs/PLATFORM_SUPPORT.md).

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
```

## Reproduce In Three Commands

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
uv run claimbound demo eea-source-audit
```

If `validate-all` passes, the committed cards and registry match the current
validators. A scaffold or demo output is not evidence until a protocol is frozen,
the run completes, the card validates and the registry is updated.

## Quick Start

```bash
uv run claimbound new
uv run claimbound demo grok-source-audit
uv run claimbound run-root \
  --protocol-id EXAMPLE_D001 \
  --source-url https://example.org/source \
  --operator your-name-or-handle
```

Non-interactive scaffold, EU runners, card protocols and operator runbooks:
[getting started](docs/GETTING_STARTED.md).

Portable AI control rules for evidence-bound work:
[12 AI Life Rules](docs/TWELVE_AI_LIFE_CONTROLS.md).

## Boundary

This repository is an independently usable open evidence foreground. It does not
include or require private background technology.

Evidence cards are reusable examples and validation records, not a hosted review
service, legal advice, or on-demand third-party check queue. The registry stores
sanitized metadata and hashes, not raw payloads.

See [governance](GOVERNANCE.md), [maintainer boundary](MAINTAINER_BOUNDARY.md) and
[release process](RELEASE_PROCESS.md).

## Community

- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Discussions](https://github.com/ClaimBound/claimbound-evidence/discussions)

## License

Apache-2.0. See [LICENSE](LICENSE).