# ClaimBound Public Benchmarks

<p align="center">
  <img
    src="docs/assets/claimbound_logo.svg"
    alt="ClaimBound public benchmarks logo"
    width="400"
  />
</p>

ClaimBound Public Benchmarks is an open-source foreground for pre-registered
public-source evidence records for narrow AI/ML claims.

It is not a production forecasting service. It is a public toolkit for checking
whether a narrow claim was tested under rules fixed before the run.

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

- Start here: [getting started](docs/GETTING_STARTED.md),
  [audience and value](docs/AUDIENCE_AND_VALUE.md) and
  [current evidence tracks](docs/CURRENT_EVIDENCE_TRACKS.md).
- Evidence rules: [result statuses](docs/RESULT_STATUS.md),
  [claim boundaries](docs/CLAIMS.md) and
  [evidence cards](docs/EVIDENCE_CARD.md).
- Operating protocols: [manual audit](docs/MANUAL_AUDIT_PROTOCOL.md) and
  [AI-assisted operation](docs/AI_OPERATOR_PROTOCOL.md).
- Project direction: [positioning](docs/PROJECT_POSITIONING.md),
  [honesty manifesto](docs/HONESTY_MANIFESTO.md) and
  [use cases](docs/USE_CASES.md).
- Automation direction: [scaffold automation plan](docs/SCAFFOLD_AUTOMATION_PLAN.md).
- Registry direction: [global evidence registry](docs/GLOBAL_EVIDENCE_REGISTRY.md).

## Install

```bash
uv sync --extra dev
uv run --extra dev python -m pytest -n auto
```

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
