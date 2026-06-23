# HEADROOM_WIDE_CLAIMS_D001 Pre-Registration Charter

Status: frozen single-operator protocol for Headroom v0.27.0 claim-boundary
evidence.

Created: 2026-06-23

## Claim Boundary

This protocol checks narrow, local, reproducible claims derived from Headroom's
wide public token-compression language. It must not be used as a general
certification of Headroom, Codex, Ollama, Qwen, Gemma or any cloud provider.

## Source Boundary

- Source name: Headroom v0.27.0 public repository and package
- Repository tag: https://github.com/headroomlabs-ai/headroom/tree/v0.27.0
- Tag commit observed before execution: `95b2333ee5a3f1cbe512ca04a6563c3572835758`
- Package: `headroom-ai==0.27.0`
- Access date: 2026-06-23
- Source rights: public Apache-2.0 repository; no private Headroom materials
  used.

## Narrow Cards

| Card ID | Narrow claim |
| --- | --- |
| `HEADROOM_SOURCE_BOUNDARY_D001` | The v0.27.0 public sources contain the wide claim and the relevant local/Ollama, Codex/proxy and memory boundaries. |
| `HEADROOM_MEMORY_NOT_REQUIRED_D001` | The local library compression path can be invoked without enabling cross-agent memory. |
| `HEADROOM_OLLAMA_JSON_TOOL_OUTPUT_D001` | A synthetic JSON tool-output fixture passes both a token-reduction gate and an exact-answer gate on local Ollama. |
| `HEADROOM_OLLAMA_LOG_OUTPUT_D001` | A synthetic structured-log fixture passes both gates on local Ollama. |
| `HEADROOM_OLLAMA_AGENT_HISTORY_D001` | A synthetic agent-history fixture passes both gates on local Ollama. |
| `HEADROOM_RAG_PLAIN_TEXT_D001` | Public sources and a local check are sufficient to treat RAG/plain text as covered by the 60-95% headline. |
| `HEADROOM_CODE_FILE_DEFAULT_D001` | Public sources and a local check are sufficient to treat source-code/file payloads as covered by the 60-95% headline. |
| `HEADROOM_CODEX_PROXY_ROUTE_D001` | The documented Codex wrapper/proxy route is visible without publishing private Codex traffic. |
| `HEADROOM_CODEX_SAME_ANSWER_D001` | A deterministic Codex original-vs-compressed same-answer run can be published without private transcript leakage. |

## Runtime Procedure

1. Use `uv run python scripts/claimbound_run_headroom_wide_claims.py`.
2. The runner may bootstrap `headroom-ai==0.27.0` and `transformers` through
   `uv --with` when they are not installed in the project environment.
3. Set `HEADROOM_TELEMETRY=off` and do not enable `--log-messages`.
4. Use local Ollama only for runtime answer checks.
5. Prefer the installed Qwen model `qwen2.5-coder:7b`; fall back to `qwen3:8b`
   only when the primary model is unavailable.
6. Do not use the local `gemma4:e2b-mlx` model as the main public claim path.
   A standard Ollama Gemma model may be added later as a separate rerun.
7. Keep raw prompts, full fixtures, model transcripts, credentials and hardware
   identifiers such as serial number, hardware UUID and provisioning UDID out of
   the public repository.

## Gates

For each runtime card:

- Baseline: original synthetic fixture sent to the same Ollama model.
- Treatment: Headroom-compressed fixture sent to the same Ollama model.
- Temperature: 0.
- Exact-answer gate: normalized model output must equal the expected synthetic
  answer.
- Token-reduction gate: `reduction_pct = tokens_saved / tokens_before * 100`.
- JSON/log/agent-history pass threshold: at least 60% reduction and both exact
  answers match.
- If the original baseline does not answer correctly, the card is insufficient
  rather than negative against Headroom.
- If the compressed path loses the exact answer, the card is negative under this
  protocol even when token reduction is high.

## Status Rules

- `PASSED_UNDER_PROTOCOL`: every frozen gate for the narrow claim passed.
- `NEGATIVE_RESULT_UNDER_PROTOCOL`: the frozen gate was fair and did not pass.
- `INSUFFICIENT_COVERAGE`: the run cannot fairly answer the narrow claim.
- Source-boundary cards may be positive only for source/documentation presence,
  not runtime behavior.

## Interpretation Rules

A negative runtime card does not mean Headroom is unusable. It means only that
the specific local Ollama fixture failed the frozen gate in this protocol.

The exact-answer gate is deliberately stricter than a general user-satisfaction
or semantic-quality benchmark. It was chosen because the checked fixtures ask
for one synthetic identifier, so an answer-preservation claim can be tested
without an LLM judge. If a Headroom deployment expects CCR retrieval tools,
proxy-specific behavior, provider-specific tool calling, or tolerant semantic
drift, that must be checked by a separate narrow card rather than inferred from
these local direct-chat results.

## Public Outputs

- Request: `docs/evidence_requests/HEADROOM_WIDE_CLAIMS_D001_REQUEST.md`
- Protocol: `docs/protocols/HEADROOM_WIDE_CLAIMS_D001_PREREG_CHARTER.md`
- Runbook: `docs/runbooks/HEADROOM_WIDE_CLAIMS_D001.md`
- Runner: `scripts/claimbound_run_headroom_wide_claims.py`
- Summaries: `artifacts/headroom_*_summary.json`
- Cards: `docs/evidence_cards/CLAIMBOUND-HEADROOM_*-2026-06-23.json`
- Registry: `docs/registry/evidence_index.json`

## Stop Conditions

Stop and record an honest non-green result when source access, package import,
Ollama availability, local model identity, token stats, answer checking or
privacy constraints prevent a fair positive card.
