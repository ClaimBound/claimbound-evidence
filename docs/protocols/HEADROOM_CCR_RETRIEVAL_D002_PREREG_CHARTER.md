# HEADROOM_CCR_RETRIEVAL_D002 prereg charter

## Protocol boundary

This protocol checks the Headroom v0.27.0 CCR/MCP recovery path on one local
machine. It is a corrective follow-up to the D001 exact-answer gates: D001
remains valid for the strict direct-compress Ollama question, but D001 does not
fully test Headroom's documented CCR workflow.

## Fixed version and sources

- Headroom package: `headroom-ai==0.27.0`
- Headroom tag: `v0.27.0`
- Tag commit: `95b2333ee5a3f1cbe512ca04a6563c3572835758`
- Access date: `2026-06-23`
- Public source files:
  - `docs/content/docs/ccr.mdx`
  - `docs/content/docs/mcp.mdx`
  - `docs/content/docs/proxy.mdx`
  - `headroom/ccr/mcp_server.py`
  - `headroom/ccr/tool_injection.py`
  - `headroom/compress.py`

## Gates

### Source boundary

Pass if fetched public sources or CLI help expose CCR/MCP compression,
`headroom_compress`, `headroom_retrieve` and `/v1/retrieve` as the documented
recoverability path.

### MCP full retrieve

Pass if:

- synthetic payload is generated in memory;
- `HeadroomMCPServer(check_proxy=False)._handle_compress()` returns a hash;
- `headroom_retrieve(hash)` returns original content;
- returned content SHA-256 equals the original fixture SHA-256;
- tokens saved is positive.

### MCP query retrieve

Pass if `headroom_retrieve(hash, query="TARGET-ALPHA CASE-0073")` returns a
result containing both `TARGET-ALPHA` and `CASE-0073`.

### Direct compress boundary

Pass if plain `compress()` reduces tokens but the compressed output does not
include a CCR marker/hash for the same fixture. This is a boundary card, not a
criticism: it prevents over-reading direct-compress answer drift as a full CCR
failure.

## Environment statement

Cards must record the user-declared local environment: MacBook Pro 16 inch,
Apple M1 Pro, 16 GB. Raw machine serials, hardware UUIDs and private paths must
not be committed.

