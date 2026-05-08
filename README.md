# ClaimBound Public Benchmarks

<p align="center">
  <img
    src="docs/assets/claimbound_logo.svg"
    alt="ClaimBound public benchmarks logo"
    width="400"
  />
</p>

ClaimBound Public Benchmarks is an open-source foreground for evidence cards:
small, checkable records for narrow public AI, ML and data claims.

It is not a production forecasting service, model leaderboard or certification
authority. It is a public toolkit for checking whether a narrow claim was tested
under rules fixed before the run.

The short version:

```text
Where is the evidence?
```

ClaimBound turns a narrow public AI, ML or data claim into a reproducible
evidence card with protocol, source lineage, hashes, result status, claim
boundary and reproduction level.

If there is no evidence card, the statement is still only a claim.

![ClaimBound workflow](docs/assets/claimbound_workflow.svg)

Start with [ClaimBound in 5 minutes](docs/CLAIMBOUND_IN_5_MINUTES.md) for the
plain-language version.

## Flagship Workflow: Public AI Transparency Claim To Evidence Card

Example public claim:

```text
xAI publishes system prompts for Grok chat assistant and product features in
the public xai-org/grok-prompts repository.
```

ClaimBound does not turn this into a broad claim that Grok is safer, better or
fully reproducible at runtime. It asks a narrower question:

```text
Can the public prompt-disclosure source boundary be verified with repository
commit, README/license presence, prompt file list and SHA-256 hashes without
copying prompt text into this repository?
```

Current ClaimBound status for this repository:

```text
PASSED_UNDER_PROTOCOL / GREEN_VALIDATED
```

This green card proves only the narrow prompt-source audit. It does not prove
that the free Grok chat runtime uses these exact prompts, does not prove hidden
server-side layers are absent, and does not prove model superiority.

See the full worked example:
[Where is the evidence? Grok claim workflow](docs/FLAGSHIP_WORKFLOW_GROK_EVIDENCE.md).
The rendered share card is available as
[SVG](docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg).

## Demo Track Cards

The first ten demonstration tracks have been scaffolded and locally assessed.
The Grok prompt-transparency and EEA public-data source-audit tracks have green
source-audit cards. The other cards currently publish honest blocked-readiness
records, not success claims. Each blocked card says what is missing before a
real pass/fail empirical result can be claimed.

| Track | Audience | Current status | Card |
| --- | --- | --- | --- |
| Grok prompt transparency | Public AI transparency verification | `PASSED_UNDER_PROTOCOL` | [JSON](docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json) / [SVG](docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg) |
| Model evaluation | AI and LLM evaluation teams | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.json) |
| Reproduction appendix | Open-science reproducibility | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.json) |
| Funding review appendix | Funding reviewers and program evaluators | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-FUNDING_REVIEW_D001-2026-05-07.json) |
| Source audit | Data stewards and public-data teams | `PASSED_UNDER_PROTOCOL` | [JSON](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg) |
| Civic claim | Civic-tech, journalism and watchdog projects | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json) |
| ML appendix | ML researchers | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.json) |
| Education reproduction | Educators | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-EDU_REPRO_D001-2026-05-07.json) |
| AI product claim | Companies with AI products | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.json) |
| Procurement claim | Independent verifiers and public buyers | `BLOCKED_SOURCE` | [JSON](docs/evidence_cards/CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.json) |

Blocked cards are useful: they show that the project refused to convert a
request or scaffold into a positive result without source access, hashes,
scoring and rerun evidence.

## Concrete Evidence Cards

| Example | What it shows | Card |
| --- | --- | --- |
| Grok prompt-source audit | A green AI-transparency source audit with a strict runtime-equivalence boundary. | [JSON](docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json) / [SVG](docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg) |
| NASA POWER D-103 | A narrow positive public-source result reproduced at outcome/gate level with source-byte drift. | [JSON](docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json) / [SVG](docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg) |
| NOAA CO-OPS D-131 | A negative result under a frozen official-source protocol. | [JSON](docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json) / [SVG](docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg) |
| EEA source audit D-001 | A green public-data source-boundary card that does not claim dataset coverage or legal approval. | [JSON](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg) |
| OpenAI GPT-5 system card | A public-document source audit for an official system-card PDF, with no model-quality claim. | [JSON](docs/evidence_cards/CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.svg) |
| Anthropic system cards | A public-document source audit for the official model system-card index. | [JSON](docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg) |
| Google DeepMind model cards | A public-document source audit for the official model-card index. | [JSON](docs/evidence_cards/CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](docs/evidence_cards/CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg) |

The project focuses on reproducibility discipline:

- source eligibility is checked before a real run;
- targets, scorers, controls and acceptance gates are fixed before execution;
- raw public-source payloads stay outside the repository;
- committed artifacts contain commands, hashes, summaries and claim boundaries;
- negative and blocked results remain first-class evidence.

## Current Evidence

The current public evidence contains one narrow positive result and multiple
negative or source-blocked records:

```text
NASA POWER D-103 passed the pre-registered gate under protocol 1.0.143 and was
independently reproduced at outcome/gate level on 2026-04-29.
```

Additional records show source lineage and negative/blocked outcomes:

- EEA Air Quality Download Service D-001: source-audit completed; the public
  download page exposed expected service and rights links. See the
  [EEA source-audit card](docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json).
- NOAA CO-OPS D-131: official-source run completed; statistical acceptance did
  not pass. See the
  [NOAA evidence card](docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json).
- NYC TLC Phase 4: official-source run completed; statistical acceptance did
  not pass.
- CDC mirror path: public mirror proof path completed, but external source
  equivalence remained unresolved.

The NASA POWER D-103 positive record has a
[shareable JSON evidence card](docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json)
and a [visual SVG card](docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg).

This does not imply a universal forecasting edge, deployment readiness, or
superiority over all statistical methods.

## How The Pipeline Works

```text
official public source
  -> local raw payload outside this repository
  -> parser and source manifest
  -> pre-registered runner
  -> baseline and control comparison
  -> result status and sanitized evidence summary
```

## Core Documents

- Start here: [ClaimBound in 5 minutes](docs/CLAIMBOUND_IN_5_MINUTES.md),
  [getting started](docs/GETTING_STARTED.md),
  [audience and value](docs/AUDIENCE_AND_VALUE.md) and
  [current evidence tracks](docs/CURRENT_EVIDENCE_TRACKS.md).
- Evidence rules: [result statuses](docs/RESULT_STATUS.md),
  [claim boundaries](docs/CLAIMS.md) and
  [evidence cards](docs/EVIDENCE_CARD.md).
- Operating protocols: [manual audit](docs/MANUAL_AUDIT_PROTOCOL.md),
  [AI-assisted operation](docs/AI_OPERATOR_PROTOCOL.md) and
  [AI workflow](docs/AI_WORKFLOW.md).
- Project direction: [positioning](docs/PROJECT_POSITIONING.md),
  [honesty manifesto](docs/HONESTY_MANIFESTO.md) and
  [use cases](docs/USE_CASES.md).
- Public workflows: [audience demonstration workflows](docs/AUDIENCE_TESTIMONIAL_WORKFLOWS.md),
  [demo tracks to evidence cards](docs/DEMO_TRACKS_TO_EVIDENCE_CARDS.md) and
  [Grok claim evidence workflow](docs/FLAGSHIP_WORKFLOW_GROK_EVIDENCE.md).
- Reproduction: [independent rerun workflow](docs/INDEPENDENT_RERUN_WORKFLOW.md).
- Automation direction: [scaffold automation plan](docs/SCAFFOLD_AUTOMATION_PLAN.md).
- Registry direction: [global evidence registry](docs/GLOBAL_EVIDENCE_REGISTRY.md).
- Next steps: [public, near-term and later scope](docs/PROJECT_NEXT_STEPS.md).

## Install

```bash
uv sync --extra dev
uv run --extra dev python -m pytest -n auto
```

## Common Commands

```bash
uv run claimbound new
uv run claimbound new-track
uv run claimbound run-root --protocol-id EXAMPLE_D001 --source-url https://example.org/source
uv run claimbound demo eea-source-audit
uv run claimbound demo grok-source-audit
uv run claimbound validate-all
```

`claimbound new` can run interactively or with flags. `claimbound demo
grok-source-audit` clones the public `xai-org/grok-prompts` repository into
`$HOME/claimbound_runs/claimbound_demo/` and writes demo reports there by
default. It records only hashes and metadata, not prompt text.

## Offline Smoke

```bash
uv run --extra dev python scripts/fetch_nasa_power.py --help
uv run --extra dev python scripts/claimbound_run_nasa_power_prereg.py --help
```

The real NASA POWER payload files used for the recorded D-103 run are not
committed. Reproduction requires downloading fresh official NASA POWER Daily
JSON payloads outside the repository and recording their hashes.

Detailed reproduction instructions are in
[docs/REPRODUCTION.md](docs/REPRODUCTION.md).

## Manual Domain Tracks

Future public-domain track runbooks are included for European air quality data:

- [No-AI manual track](docs/manual_audit/EEA_AQ_D001_MANUAL_TRACK.md)
- [AI-assisted autonomous prompt](docs/manual_audit/EEA_AQ_D001_AI_ASSISTED_TRACK.md)

These runbooks are designed for operator audits: rules first, then source
download, then run, then publish the exact result status.

## Evidence Cards And Registry Direction

ClaimBound records are intended to become compact evidence cards: protocol ID,
source, access date, result status, claim boundary, hashes, git commit and
reproduction level.

The current examples are listed in
[docs/evidence_cards/README.md](docs/evidence_cards/README.md). The public
registry index is [docs/registry/evidence_index.json](docs/registry/evidence_index.json).
The SVG share-card template is
[docs/assets/claimbound_evidence_card.svg](docs/assets/claimbound_evidence_card.svg).

The long-term direction is a small global evidence registry for narrow
pre-registered public results. The registry should store sanitized cards and
hashes, not raw payloads. Blockchain, token, wallet, on-chain storage and chain
timestamp features are outside the current roadmap and have no scheduled review
date. The core trust model remains public code, source lineage, frozen gates and
independent reproduction.

## Boundary

This repository is independently usable as an open benchmark foreground. It does
not include, import, or require private background technology.

## Community

- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Discussions — maintainer announcements and community Q&A](https://github.com/ClaimBound/claimbound-public-benchmarks/discussions)

## License

Apache-2.0. See [LICENSE](LICENSE).
