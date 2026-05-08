# SOURCE_AUDIT_D001 Pre-Registration Charter

Status: frozen source-audit protocol for the 2026-05-08 EEA source-boundary run.

Created: 2026-05-07

## Claim Boundary

This track checks only a narrow `source_audit` claim for the source listed
below: whether the EEA Air Quality Portal download page is reachable and exposes
expected download-service and rights links. It must not claim dataset coverage,
legal certification, pollutant/time completeness, broad model superiority,
deployment readiness, or correctness outside this protocol.

## Source

- Source name: EEA Air Quality Download Service
- Source URL: https://aqportal.discomap.eea.europa.eu/download-data/
- Domain: public-data
- Audience: Data stewards and public-data teams
- Execution mode: MANUAL_NO_AI

## Frozen Pass Gate

The source audit passes only when all of these are true:

- source URL returns HTTP 200;
- content type is HTML;
- page title contains `Download data`;
- page exposes the current Air Quality Download Service direct link;
- page exposes the EEA copyright notice link;
- raw HTML and downloadable datasets are not committed to this repository.

## Stop Conditions

Stop and record an honest blocked or insufficient status when source access,
rights, coverage, prompt disclosure, model identity, scoring, logs or hashes are
not good enough for a fair run.
