# GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001 Pre-Registration Charter

Status: public protocol record for source-audit reruns. Existing card:
[CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08](../evidence_cards/CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.json).

Protocol version:

```text
PUBLIC-DOC-SOURCE-AUDIT-2026-05-08
```

## Claim Boundary

This protocol can check only whether the official Google DeepMind model-card
page is publicly reachable at access time and can be recorded with source
metadata and SHA-256. It must not claim model safety, model quality, benchmark
performance, runtime behavior, legal approval or deployment readiness.

## Source

```text
Official source name: Google DeepMind Model Cards
Official source URL: https://deepmind.google/models/model-cards
Expected content type: text/html
Expected markers: Google, Gemini, Model cards
Raw payload committed: false
```

## Pass Gate

Record `PASSED_UNDER_PROTOCOL` only when:

- HTTP status is 200;
- final URL is recorded;
- content type is HTML;
- required markers are present;
- byte size is recorded;
- SHA-256 is recorded;
- raw page content is not committed;
- claim boundary and known limitations are included.

## Block Conditions

Record `BLOCKED_SOURCE` when the source cannot be reached, expected markers are
missing, source metadata cannot be recorded or raw-payload policy cannot be
honored.

## Forbidden Claims

Do not claim:

- Gemini model quality or safety was verified;
- runtime behavior was verified;
- benchmark superiority;
- deployment readiness;
- legal permission for reuse.
