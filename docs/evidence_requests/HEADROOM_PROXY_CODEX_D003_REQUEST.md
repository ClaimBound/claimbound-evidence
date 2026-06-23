# HEADROOM_PROXY_CODEX_D003 request

## Request

Create a third Headroom evidence iteration for the proxy/Codex boundary. The
goal is to test local proxy compression without publishing private Codex
transcripts, and to separate "proxy compresses" from "proxy returns a CCR hash
that can be retrieved."

## Narrow claims

1. Local Headroom proxy `/v1/compress` compresses a synthetic payload and reports
   positive token savings without contacting an upstream LLM.
2. Local Headroom proxy `/v1/compress` provides a CCR hash that allows
   `/v1/retrieve` to recover original content, or the card records a negative
   result if no hash is exposed.
3. Headroom exposes public Codex proxy/wrap route signals, but this protocol does
   not prove real Codex answer equivalence or publish private transcripts.

## Ollama/local interpretation

For local Ollama, token savings do not directly mean money savings because
tokens are not billed by a cloud provider. The useful local claim is narrower:
compression may help fit larger tool outputs into the model context window and
may reduce local prompt processing load. This is only practically useful when
the workflow preserves recoverability via CCR/retrieve or the task tolerates
lossy compression.

