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

| Visual color | Chip / field | Meaning |
| --- | --- | --- |
| Green | Result status | `PASSED_UNDER_PROTOCOL` or `REPRODUCED_OUTCOME` |
| Green | Reproduction | `REPRODUCED_OUTCOME` |
| Yellow | Reproduction | `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` |
| Amber | Result status | `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE` |
| Red | Result status | `NEGATIVE_RESULT_UNDER_PROTOCOL` or invalid/tamper states |
| Blue | Reproduction | `not independently reproduced` |
| Gray | Drafts, requests and scaffolds | Not evidence yet. |

Source-byte drift belongs in `reproduction_level`, not in `result_status`.

## Current Cards By Audience

| Audience / category | What this category checks | Current cards | Status |
| --- | --- | --- | --- |
| Public AI transparency readers | Public source documentation for AI systems and model cards. | [Anthropic system cards JSON](CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg)<br>[OpenAI GPT-5 system-card JSON](CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.svg)<br>[Google DeepMind model cards JSON](CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg)<br>[Grok prompts JSON](CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json) / [SVG](CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg) | `PASSED_UNDER_PROTOCOL` |
| AI and LLM evaluation teams | Whether model-eval claims have enough model, prompt, transcript and scoring evidence. | [Model evaluation JSON](CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.json) / [SVG](CLAIMBOUND-MODEL_EVAL_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| AI tooling and agent-infra users | Whether Headroom v0.27.0 wide token-compression claims stay inside narrow local evidence boundaries. | [Source boundary JSON](CLAIMBOUND-HEADROOM_SOURCE_BOUNDARY_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_SOURCE_BOUNDARY_D001-2026-06-23.svg)<br>[Memory boundary JSON](CLAIMBOUND-HEADROOM_MEMORY_NOT_REQUIRED_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_MEMORY_NOT_REQUIRED_D001-2026-06-23.svg)<br>[Ollama JSON gate JSON](CLAIMBOUND-HEADROOM_OLLAMA_JSON_TOOL_OUTPUT_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_OLLAMA_JSON_TOOL_OUTPUT_D001-2026-06-23.svg)<br>[Ollama log gate JSON](CLAIMBOUND-HEADROOM_OLLAMA_LOG_OUTPUT_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_OLLAMA_LOG_OUTPUT_D001-2026-06-23.svg)<br>[Ollama history gate JSON](CLAIMBOUND-HEADROOM_OLLAMA_AGENT_HISTORY_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_OLLAMA_AGENT_HISTORY_D001-2026-06-23.svg)<br>[RAG/plain-text boundary JSON](CLAIMBOUND-HEADROOM_RAG_PLAIN_TEXT_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_RAG_PLAIN_TEXT_D001-2026-06-23.svg)<br>[Code/file boundary JSON](CLAIMBOUND-HEADROOM_CODE_FILE_DEFAULT_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_CODE_FILE_DEFAULT_D001-2026-06-23.svg)<br>[Codex route boundary JSON](CLAIMBOUND-HEADROOM_CODEX_PROXY_ROUTE_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_CODEX_PROXY_ROUTE_D001-2026-06-23.svg)<br>[Codex same-answer JSON](CLAIMBOUND-HEADROOM_CODEX_SAME_ANSWER_D001-2026-06-23.json) / [SVG](CLAIMBOUND-HEADROOM_CODEX_SAME_ANSWER_D001-2026-06-23.svg) | Source/memory/RAG/code boundaries: `PASSED_UNDER_PROTOCOL`<br>Ollama runtime gates: `NEGATIVE_RESULT_UNDER_PROTOCOL`<br>Codex cards: `INSUFFICIENT_COVERAGE` |
| Companies with AI products | Whether public product claims can become customer-readable evidence cards. | [AI product claim JSON](CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.json) / [SVG](CLAIMBOUND-AI_PRODUCT_CLAIM_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Independent verifiers and public buyers | What is independently checkable before an AI procurement or adoption decision. | [Procurement AI JSON](CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.json) / [SVG](CLAIMBOUND-PROCUREMENT_AI_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Data stewards and public-data teams | Official source pages, rights notes and raw-payload policy. | [EEA source audit JSON](CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json) / [SVG](CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.svg)<br>[EEA content reuse FAQ JSON](CLAIMBOUND-EEA_LEGAL_REUSE_SOURCE_AUDIT_D001-2026-06-10.json) / [SVG](CLAIMBOUND-EEA_LEGAL_REUSE_SOURCE_AUDIT_D001-2026-06-10.svg)<br>[EU Data Portal JSON](CLAIMBOUND-EU_ODP_SOURCE_AUDIT_D001-2026-06-10.json) / [SVG](CLAIMBOUND-EU_ODP_SOURCE_AUDIT_D001-2026-06-10.svg)<br>[Eurostat API guidelines JSON](CLAIMBOUND-EUROSTAT_SOURCE_AUDIT_D001-2026-06-10.json) / [SVG](CLAIMBOUND-EUROSTAT_SOURCE_AUDIT_D001-2026-06-10.svg)<br>[EEA AQ manual track JSON](CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.json) / [SVG](CLAIMBOUND-EEA-AQ-D001-MANUAL-2026-05-11.svg) | EU source audits: `PASSED_UNDER_PROTOCOL`<br>Manual track: `BLOCKED_SOURCE` |
| Civic tech, journalism and watchdogs | Official-data claims about mobility, public services or infrastructure. | [Civic claim JSON](CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json) / [SVG](CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Open science and reproducibility teams | Whether a published result can be rerun, including negative or drift outcomes. | [NASA POWER D-103 JSON](CLAIMBOUND-NASA-POWER-D103-2026-04-29.json) / [SVG](CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg)<br>[NASA POWER D-103 rerun JSON](CLAIMBOUND-NASA-POWER-D103-RERUN-2026-06-15.json) / [SVG](CLAIMBOUND-NASA-POWER-D103-RERUN-2026-06-15.svg)<br>[NOAA CO-OPS D-131 JSON](CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json) / [SVG](CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg)<br>[NOAA CO-OPS D-131 rerun JSON](CLAIMBOUND-NOAA-COOPS-D131-RERUN-2026-06-15.json) / [SVG](CLAIMBOUND-NOAA-COOPS-D131-RERUN-2026-06-15.svg)<br>[Reproduction appendix JSON](CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.json) / [SVG](CLAIMBOUND-REPRO_APPENDIX_D001-2026-05-07.svg) | NASA: `PASSED_UNDER_PROTOCOL`, drift in `reproduction_level`<br>NOAA: `NEGATIVE_RESULT_UNDER_PROTOCOL`, drift in `reproduction_level`<br>Baseline NASA/NOAA cards may show `SINGLE_OPERATOR_RERUN` after maintainer re-verify; sibling rows are `reproduction_attempt` cards<br>Repro appendix: `BLOCKED_SOURCE` |
| ML researchers | Narrow method appendices with controls, baselines and claim boundaries. | [ML appendix JSON](CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.json) / [SVG](CLAIMBOUND-ML_APPENDIX_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Educators | Small classroom reproducibility exercises. | [Education reproduction JSON](CLAIMBOUND-EDU_REPRO_D001-2026-05-07.json) / [SVG](CLAIMBOUND-EDU_REPRO_D001-2026-05-07.svg) | `BLOCKED_SOURCE` |
| Software developers and maintainers | Whether a narrow validator or regression gate passed under frozen commands. | [Software dev validator gate JSON](CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json) / [SVG](CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.svg)<br>[API parity registry gate JSON](CLAIMBOUND-API_PARITY_D001-2026-06-15.json) / [SVG](CLAIMBOUND-API_PARITY_D001-2026-06-15.svg) | `PASSED_UNDER_PROTOCOL` |

## Advanced Examples (Not First-Screen Cards)

These registry cards illustrate optional patterns. They are **not** programme
selection, endorsement or approval evidence. They stay in the registry for
methodology transparency but are excluded from first-screen reviewer paths in
[REVIEWER_SUMMARY.md](../REVIEWER_SUMMARY.md) and
[CURRENT_EVIDENCE_TRACKS.md](../CURRENT_EVIDENCE_TRACKS.md#advanced-optional-tracks).

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
