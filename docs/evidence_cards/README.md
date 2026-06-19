# Evidence Cards

Evidence cards are the public share unit for ClaimBound results.

Each card is a compact JSON record that points to:

- the frozen protocol;
- the public source boundary;
- the sanitized result artifact;
- the exact result status;
- the claim boundary;
- the reproduction level.

The SVG preview is rendered from the JSON card. Do not edit rendered SVG cards
by hand after the result is known.

## Card Versus Artifact Versus Scaffold

| Type | In [registry](../registry/evidence_index.json)? | Meaning |
| --- | --- | --- |
| Evidence card | Yes | Frozen protocol, exact status, claim boundary, validated JSON/SVG |
| Artifact-only | No | Useful run output without full card promotion — see [artifacts catalog](../artifacts/README.md) |
| Scaffold | No | Gray draft from `claimbound new`; not evidence |

## Color Semantics

Color is a reading aid, not a second result system.

| Visual color | Used for | Meaning |
| --- | --- | --- |
| Green | `PASSED_UNDER_PROTOCOL`, `REPRODUCED_OUTCOME`, `GREEN_VALIDATED` | The narrow card or validation gate passed. |
| Yellow | `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`, limited reproducibility | The outcome is useful, but reproduction has an important limitation. |
| Amber | `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE` | No empirical success or failure should be claimed. |
| Red | `NEGATIVE_RESULT_UNDER_PROTOCOL` or invalid/tamper states | The protocol ran and the claim did not pass, or the card is invalid. |
| Gray | Drafts, requests and scaffolds | Not evidence yet. |

## Current Cards By Audience

| Audience / category | What this category checks | Current cards | Status |
| --- | --- | --- | --- |
| Public AI transparency readers | Public source documentation for AI systems and model cards. | [Anthropic system cards JSON](CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg)<br>[OpenAI GPT-5 system-card JSON](CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.svg)<br>[Google DeepMind model cards JSON](CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg)<br>[Grok prompts JSON](CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json) / [SVG](CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg) | `PASSED_UNDER_PROTOCOL` |
| AI and LLM evaluation teams | Whether model-eval claims have enough model, prompt, transcript and scoring evidence. | [Model evaluation JSON](CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.json) / [SVG](CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Companies with AI products | Whether public product claims can become customer-readable evidence cards. | [AI product claim JSON](CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.json) / [SVG](CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Independent verifiers and public buyers | What is independently checkable before an AI procurement or adoption decision. | [Procurement AI JSON](CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.json) / [SVG](CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Data stewards and public-data teams | Official source pages, rights notes and raw-payload policy. | [EEA source audit JSON](CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg)<br>[EEA AQ manual track JSON](CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.json) / [SVG](CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.svg) | Source audit: `PASSED_UNDER_PROTOCOL`<br>Manual track: `BLOCKED_SOURCE` |
| Civic tech, journalism and watchdogs | Official-data claims about mobility, public services or infrastructure. | [Civic claim JSON](CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json) / [SVG](CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Open science and reproducibility teams | Whether a published result can be rerun, including negative or drift outcomes. | [NASA POWER D-103 JSON](CLAIMBOUND-NASA-POWER-D103-2026-04-29.json) / [SVG](CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg)<br>[Reproduction appendix JSON](CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.json) / [SVG](CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.svg)<br>[NOAA CO-OPS D-131 JSON](CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json) / [SVG](CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg) | NASA: `PASSED_UNDER_PROTOCOL` with source-byte drift<br>NOAA: `NEGATIVE_RESULT_UNDER_PROTOCOL`<br>Repro appendix: `BLOCKED_SOURCE` |
| ML researchers | Narrow method appendices with controls, baselines and claim boundaries. | [ML appendix JSON](CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.json) / [SVG](CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Educators | Small classroom reproducibility exercises. | [Education reproduction JSON](CLAIMBOUND-EDU_REPRO_D001-2026-05-07.json) / [SVG](CLAIMBOUND-EDU_REPRO_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Software developers and maintainers | Whether a narrow validator or regression gate passed under frozen commands. | [Software dev validator gate JSON](CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json) / [SVG](CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.svg) | `PASSED_UNDER_PROTOCOL` |

## Advanced Examples (Not First-Screen Cards)

These registry cards illustrate optional patterns. They are **not** programme
selection, endorsement or approval evidence.

| Pattern | Cards | Status | Read next |
| --- | --- | --- | --- |
| Program review appendix | [Program review JSON](CLAIMBOUND-PROGRAM_REVIEW_D001-2026-05-07.json) / [SVG](CLAIMBOUND-PROGRAM_REVIEW_D001-2026-05-07.svg) | `BLOCKED_SOURCE` | Shows when a review appendix is not ready for an empirical claim. |
| Applicant-side eligibility self-check | [Program-fit self-check JSON](CLAIMBOUND-PROGRAM_FIT_D001-2026-06-04.json) / [SVG](CLAIMBOUND-PROGRAM_FIT_D001-2026-06-04.svg) | `PASSED_UNDER_PROTOCOL`, single-operator only | [Program eligibility self-check example](../examples/PROGRAM_ELIGIBILITY_SELF_CHECK.md) — methodology demo only; not program endorsement. |

## What The Mix Shows

The current registry contains positive, negative, blocked and limited
reproduction outcomes. That is intentional:

- green cards show that a narrow public source or result passed;
- red cards show that a claim can fail honestly under fixed rules;
- amber cards show that a source was not good enough for a fair result;
- yellow drift cards show why reproduction needs exact source-boundary notes.

This makes the project more credible than a repository that publishes only
successful outcomes.

## Registry

The public registry index is
[docs/registry/evidence_index.json](../registry/evidence_index.json).

The registry is intended to remain freely readable. It stores card metadata and
aggregate statistics, not raw payloads.
