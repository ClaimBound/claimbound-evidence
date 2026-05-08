# Evidence Cards

Evidence cards are the public share unit for ClaimBound results.

Each card is a compact JSON record that points to:

- the frozen protocol;
- the public source boundary;
- the sanitized result artifact;
- the exact result status;
- the claim boundary;
- the reproduction level.

The card is designed to be copied as a URL, attached to a discussion, or listed
in a public registry. It is not a certificate and does not imply approval
outside the documented protocol.

## Current Examples

| Card | Status | Source |
| --- | --- | --- |
| [AI product claim JSON](CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.json) / [SVG](CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | xAI Grok 4 public announcement |
| [Civic claim JSON](CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json) / [SVG](CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | NYC TLC Trip Record Data |
| [Education reproduction JSON](CLAIMBOUND-EDU_REPRO_D001-2026-05-07.json) / [SVG](CLAIMBOUND-EDU_REPRO_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | NASA POWER Daily point API |
| [Funding review JSON](CLAIMBOUND-FUNDING_REVIEW_D001-2026-05-07.json) / [SVG](CLAIMBOUND-FUNDING_REVIEW_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | ClaimBound public repository |
| [Google DeepMind model cards JSON](CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg) | `PASSED_UNDER_PROTOCOL` | Google DeepMind Model Cards |
| [Grok prompts source audit JSON](CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json) / [SVG](CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg) | `PASSED_UNDER_PROTOCOL` | xAI grok-prompts repository |
| [ML appendix JSON](CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.json) / [SVG](CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | NASA POWER Daily point API |
| [Model evaluation JSON](CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.json) / [SVG](CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | xAI Grok 4 API documentation |
| [NASA POWER D-103 JSON](CLAIMBOUND-NASA-POWER-D103-2026-04-29.json) / [SVG](CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg) | `PASSED_UNDER_PROTOCOL` | NASA POWER |
| [NOAA CO-OPS D-131 JSON](CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json) / [SVG](CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg) | `NEGATIVE_RESULT_UNDER_PROTOCOL` | NOAA CO-OPS |
| [OpenAI GPT-5 system-card JSON](CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.svg) | `PASSED_UNDER_PROTOCOL` | OpenAI GPT-5 System Card PDF |
| [Procurement AI JSON](CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.json) / [SVG](CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | xAI Grok 4 API documentation |
| [Reproduction appendix JSON](CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.json) / [SVG](CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | ClaimBound NASA POWER D-103 evidence card |
| [EEA source audit JSON](CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg) | `PASSED_UNDER_PROTOCOL` | EEA Air Quality Download Service |
| [Anthropic system cards JSON](CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg) | `PASSED_UNDER_PROTOCOL` | Anthropic Model System Cards |

## Visual Template

The visual share-card template is stored at
[docs/assets/claimbound_evidence_card.svg](../assets/claimbound_evidence_card.svg).

The SVG contains placeholder fields such as `{{record_id}}`,
`{{status_exact}}` and `{{allowed_claim_sentence}}`. A rendered card should be
filled from a validated JSON evidence card, not edited by hand after the result
is known.

To share a result, use either the JSON URL for machine-readable evidence or the
SVG URL for a human-readable card preview.

## Registry

The public registry index is
[docs/registry/evidence_index.json](../registry/evidence_index.json).

The registry is intended to remain freely readable. It stores card metadata and
aggregate statistics, not raw payloads.
