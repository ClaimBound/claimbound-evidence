# EUROSTAT_SOURCE_AUDIT_D001 Pre-Registration Charter

Status: frozen source-audit protocol for the 2026-06-10 Eurostat API guidelines run.

Created: 2026-06-10

## Claim Boundary

This track checks only a narrow `source_audit` claim for the Eurostat API
detailed guidelines page: whether the page is reachable and exposes expected
copyright and catalogue API documentation links. It must not claim statistical
coverage, API availability at runtime or correctness outside this protocol.

## Source

- Source name: Eurostat API detailed guidelines
- Source URL: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines
- Domain: public-data
- Audience: European public-data stewards and civic analysts
- Execution mode: AUTOMATED_AI_ASSISTED

## Frozen Pass Gate

The source audit passes only when all of these are true:

- source URL returns HTTP 200;
- content type is HTML;
- page title contains `API - Detailed guidelines`;
- page exposes the Eurostat copyright notice link;
- page exposes catalogue API DCAT documentation link;
- page exposes catalogue API Metabase documentation link;
- raw HTML is not committed to this repository.

## Stop Conditions

Stop and record an honest blocked status when source access, link presence or
hashes are not good enough for a fair run.
