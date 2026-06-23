# HEADROOM_SEMANTIC_FIDELITY_D004 request

## Request

Create a fourth Headroom evidence iteration that replaces exact-string answer
matching with a same-meaning structured-field gate.

## Narrow claims

1. For a synthetic JSON tool-output fixture, Headroom local compression plus
   Ollama preserves the predeclared semantic fields while reducing input tokens
   by at least 60%.
2. For a synthetic structured-log fixture, Headroom local compression plus
   Ollama preserves the predeclared semantic fields while reducing input tokens
   by at least 60%.
3. For a synthetic agent-history fixture, Headroom local compression plus Ollama
   preserves the predeclared semantic fields while reducing input tokens by at
   least 60%.

## Gate distinction

This is not an exact-answer protocol. Wording may differ. The gate only checks
whether predeclared structured facts match:

- IDs and codes;
- request IDs or note numbers;
- status fields;
- no LLM judge.

## Non-goals

- No LinkedIn article is prepared or published from this protocol.
- No claim that all Headroom outputs preserve meaning.
- No raw prompts, full synthetic fixtures or LLM transcripts are committed.

