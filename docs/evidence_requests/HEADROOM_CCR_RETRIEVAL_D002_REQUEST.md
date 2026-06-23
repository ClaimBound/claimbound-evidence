# HEADROOM_CCR_RETRIEVAL_D002 request

## Request

Create a second Headroom evidence iteration that checks the documented CCR
(Compress-Cache-Retrieve) path instead of treating direct compressed prompts as
the whole product claim.

## Narrow claims

1. Headroom v0.27.0 public docs/source expose CCR/MCP compression,
   `headroom_retrieve` and proxy retrieve endpoints as the documented recovery
   path.
2. Local MCP `headroom_compress` stores a synthetic JSON payload and
   `headroom_retrieve(hash)` returns byte-identical content.
3. Local MCP `headroom_retrieve(hash, query)` returns the known synthetic target
   row for a deterministic query.
4. Plain library `compress()` is a non-CCR boundary for this fixture: it reduces
   tokens but does not expose a retrieve hash, so direct-compress exact-answer
   failures must not be used as the full CCR verdict.

## Non-goals

- No claim that Headroom is certified.
- No claim that Codex private traffic was captured or inspected.
- No claim that all LLM answers remain text-identical.
- No raw transcripts, raw synthetic fixtures or private local identifiers in the
  public artifacts.

