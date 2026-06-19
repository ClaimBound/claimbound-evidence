# Case Study: EEA Air Quality Source Audit (D001)

This walkthrough shows how one European public-data claim becomes an inspectable
evidence card. It is a teaching example, not legal advice or EEA endorsement.

## The narrow claim

```text
The official EEA Air Quality download page is reachable and exposes expected
download-service and rights links on the access date.
```

Card: [CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08](../evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json)

## What the protocol froze before the outcome

| Control | Expectation |
| --- | --- |
| HTTP status | 200 |
| Content type | text/html |
| Page title | Download data |
| Service link | Current Air Quality Download Service |
| Rights link | EEA copyright notice |

Protocol id: `SOURCE_AUDIT_D001` · version `SOURCE-AUDIT-2026-05-08`

## What ran

```bash
uv run python scripts/claimbound_run_eea_source_audit.py \
  --report artifacts/source_audit_d001_summary.json
```

Raw HTML and datasets were **not** committed. The card records a sanitized
summary SHA-256 and a page hash in `raw_payload_manifest`.

## Outcome

| Field | Value |
| --- | --- |
| `result_status` | `PASSED_UNDER_PROTOCOL` |
| `verification_level` | `SINGLE_OPERATOR` |
| `reproduction_level` | `not independently reproduced` |

SVG preview:
[CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg](../evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg)

## Claim boundary (what you must not infer)

From the card `claim_boundary`:

- no dataset download or coverage claim,
- no pollutant or station completeness claim,
- no legal redistribution conclusion.

## Honest blocked sibling example

The larger EEA AQ manual track was stopped as `BLOCKED_SOURCE` when the public
URL manifest was incomplete:
[CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11](../evidence_cards/CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.json).

Blocked stops are first-class evidence — they prevent overclaiming.

## Operator rerun and drift

Check whether the live page bytes changed:

```bash
uv run claimbound drift eea-source-audit
```

External operators closing VERIFY #88 should follow
[Tier B — EEA drift](../external_verification/TIER_B_EEA_DRIFT.md).

Drift updates reproduction metadata; it does not automatically invalidate the
original gate without protocol evidence.

## European context

Five EU-related examples and explicit limits:
[European Dimension](../EUROPEAN_DIMENSION.md).

## Try it yourself (15 minutes)

[Start without coding](../START_WITHOUT_CODING.md) ·
[Reviewer path](../REVIEWER_PATH.md)