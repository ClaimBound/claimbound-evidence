# EEA_LEGAL_REUSE_SOURCE_AUDIT_D001 Pre-Registration Charter

Status: frozen source-audit protocol for the 2026-06-10 EEA reuse FAQ run.

Created: 2026-06-10

## Claim Boundary

This track checks only a narrow `source_audit` claim for the EEA FAQ page on
reusing EEA content: whether the page is reachable and exposes expected legal
notice and FAQ navigation links. It must not claim legal eligibility to reuse
content, institutional endorsement or correctness outside this protocol.

## Source

- Source name: EEA content reuse FAQ
- Source URL: https://www.eea.europa.eu/en/about/contact-us/faqs/can-i-use-eea-content-in-my-work-or-in-my-organisations-products
- Domain: public-data
- Audience: European public-data stewards and civic analysts
- Execution mode: AUTOMATED_AI_ASSISTED

## Frozen Pass Gate

The source audit passes only when all of these are true:

- source URL returns HTTP 200;
- content type is HTML;
- page title contains `Can I use EEA content`;
- page exposes a legal-notice navigation link;
- page exposes an FAQs index navigation link;
- raw HTML is not committed to this repository.

## Stop Conditions

Stop and record an honest blocked status when source access, link presence or
hashes are not good enough for a fair run.
