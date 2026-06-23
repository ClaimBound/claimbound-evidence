# Evidence Request: HEADROOM_WIDE_CLAIMS_D001

Status: accepted for single-operator local evidence run.

## Public Claim

Headroom publicly presents a wide token-compression claim: 60-95% fewer tokens,
same answers, across agent-read context such as tool outputs, logs, RAG chunks,
files and conversation history, with library, proxy, MCP, Codex and local-first
paths.

## Claim Source URL

https://github.com/headroomlabs-ai/headroom/tree/v0.27.0

## Narrow ClaimBound Question

Which parts of the wide Headroom claim can be checked under a frozen local
protocol, and which parts should become negative or insufficient evidence rather
than a broad success statement?

## Main Audience

AI-tool maintainers, LLM-agent users, Headroom maintainers and external
operators who may rerun or challenge the cards.

## Preferred Track

`AUTOMATED_AI_ASSISTED` single-operator public evidence run with synthetic local
fixtures, local Ollama, sanitized artifacts and no raw transcripts committed.

## Proposed Sources

- Headroom v0.27.0 repository tag:
  https://github.com/headroomlabs-ai/headroom/tree/v0.27.0
- PyPI package used by the run: `headroom-ai==0.27.0`
- Local Ollama endpoint on the operator machine.

## Proposed Scoring Or Resolution Rule

The wide claim is split into narrow cards. Runtime cards compare original
messages against Headroom-compressed messages on the same local Ollama model,
temperature 0, with deterministic exact-answer checks and pre-declared token
reduction gates.

## Known Reproducibility Risks

- Headroom source, package and docs may drift after v0.27.0.
- Local Ollama model behavior can vary by model build, context window and
  hardware.
- Codex route checks cannot publish private Codex transcripts.
- CCR retrieval markers may require an additional retrieval tool path; a
  compressed prompt without retrieval may not preserve answerability.
- Token counts depend on the model tokenizer and Headroom package behavior.

## Claims This Track Must Not Make

- no endorsement by Headroom maintainers;
- no general quality, safety or reliability certification;
- no claim that one local model run covers every provider;
- no claim that token savings imply answer preservation;
- no claim that a green source-boundary card proves runtime behavior.
