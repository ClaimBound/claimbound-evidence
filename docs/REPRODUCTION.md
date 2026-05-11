# Reproduction Guide

This guide explains how to reproduce the current NASA POWER D-103 evidence and
how to run a future manual public-domain audit without tuning after seeing the
result.

## General Rule

Fix the protocol first. Then download data. Then run. Then publish the exact
result, even when it is negative or source-blocked.

## Environment

```bash
uv sync --extra dev
uv run pytest -n auto
```

## NASA POWER D-103

Current protocol:

```text
docs/protocols/NASA_POWER_D103_PREREG_CHARTER.md
```

Raw NASA POWER JSON payloads are not committed. Download fresh official payloads
outside the repository and record their SHA-256 hashes.

Official NASA POWER references:

- https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- https://power.larc.nasa.gov/docs/referencing/

Run:

```bash
uv run python scripts/claimbound_run_nasa_power_prereg.py \
  --point POWER_A --json /path/outside/repo/POWER_A.json \
  --point POWER_B --json /path/outside/repo/POWER_B.json \
  --point POWER_C --json /path/outside/repo/POWER_C.json \
  --report /path/outside/repo/nasa_power_d103_report.json
```

Record:

```bash
shasum -a 256 /path/outside/repo/*.json
shasum -a 256 /path/outside/repo/nasa_power_d103_report.json
```

Interpretation:

- same gate outcome and status: outcome/gate reproduction;
- different raw payload hashes: source-byte drift;
- different gate outcome: record the mismatch and do not claim reproduction.

## EEA Manual Public-Domain Track

The EEA AQ D-001 manual track is the current public-domain manual example. The
repository includes a blocked-source manifest card and a reusable runner. A
future operator can still complete the raw-payload coverage path outside the
repository.

Official references:

- https://aqportal.discomap.eea.europa.eu/download-data/
- https://www.eea.europa.eu/legal
- https://www.eea.europa.eu/en/about/contact-us/faqs/can-i-use-eea-content-in-my-work-or-in-my-organisations-products

Suggested protocol ID:

```text
EEA_AQ_D001
```

Suggested first pollutant:

```text
PM10
```

Suggested source rule:

```text
Use stations from NL, BE and DE with at least 85% daily coverage over
2018-01-01 through 2024-12-31. Select the first five eligible stations sorted by
country code, locality and station identifier. Do not replace stations after
outcome inspection.
```

Suggested target:

```text
Future high-pollution event over the next 7 days, defined by the training-only
90th percentile of daily PM10.
```

Suggested candidate:

```text
Current PM10 anomaly z-score, with train-only mean and standard deviation.
```

Suggested controls:

- persistence;
- rolling 7-day mean;
- rolling 30-day mean;
- seasonal day-of-year baseline;
- EWMA residual;
- shuffled candidate;
- time-reversed candidate.

Stop and record a blocked or negative result if:

- source rights are unclear;
- source payload cannot be hashed;
- station list changes after outcome inspection;
- thresholds change after outcome inspection;
- too many values are missing;
- too few events are present;
- a negative control beats the candidate;
- the result only passes after deleting weak windows.

Current manifest probe:

```bash
python3 scripts/claimbound_run_eea_manual_track.py \
  --probe-eea-api \
  --report artifacts/eea_aq_d001_manual_summary.json
```

Current public card:

```text
docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.json
```

The manual checklist is in:

```text
docs/manual_audit/EEA_AQ_D001_MANUAL_TRACK.md
```
