# EU_ODP_SOURCE_AUDIT_D001 Pre-Registration Charter

Status: frozen source-audit protocol for the 2026-06-10 European Data Portal run.

Created: 2026-06-10

## Claim Boundary

This track checks only a narrow `source_audit` claim for the source listed
below: whether the European Data Portal landing page is reachable and exposes
expected dataset catalog, search API and copyright notice links. It must not
claim catalogue completeness, dataset quality, legal redistribution rights or
correctness outside this protocol.

## Source

- Source name: European Data Portal (data.europa.eu)
- Source URL: https://data.europa.eu/en
- Domain: public-data
- Audience: European public-data stewards and civic analysts
- Execution mode: AUTOMATED_AI_ASSISTED

## Frozen Pass Gate

The source audit passes only when all of these are true:

- source URL returns HTTP 200;
- content type is HTML;
- page title contains `European Data Portal`;
- page exposes the dataset catalog link;
- page exposes the hub search API link;
- page exposes the copyright notice link;
- raw HTML and downloadable datasets are not committed to this repository.

## Stop Conditions

Stop and record an honest blocked status when source access, link presence or
hashes are not good enough for a fair run.
