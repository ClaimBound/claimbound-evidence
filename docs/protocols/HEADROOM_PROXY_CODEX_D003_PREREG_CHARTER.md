# HEADROOM_PROXY_CODEX_D003 prereg charter

## Protocol boundary

This protocol checks Headroom v0.27.0 local proxy compression and Codex route
surface. It does not capture private Codex traffic and does not claim Codex
compatibility unless a future protocol can safely reproduce route behavior and
answer comparison.

## Fixed version and sources

- Headroom package: `headroom-ai==0.27.0`
- Headroom tag: `v0.27.0`
- Tag commit: `95b2333ee5a3f1cbe512ca04a6563c3572835758`
- Access date: `2026-06-23`

## Gates

### Proxy compression endpoint

Pass if an in-process ASGI proxy call to `/v1/compress` returns HTTP 200 and
positive token savings for the deterministic synthetic fixture.

### Proxy CCR hash retrieve

Pass only if `/v1/compress` exposes a CCR hash or marker and `/v1/retrieve`
returns byte-identical original content. If compression succeeds but no hash is
exposed, record `NEGATIVE_RESULT_UNDER_PROTOCOL` for this narrow claim.

### Codex proxy boundary

Always avoid private transcript publication. Public source and CLI route signals
may be recorded, but without a reproducible Codex traffic comparison the result
must remain `INSUFFICIENT_COVERAGE`.

## Privacy controls

- Do not enable `--log-messages`.
- Do not commit raw request bodies, raw compressed bodies or private Codex
  transcripts.
- Do not commit local proxy SQLite paths, serial numbers, hardware UUIDs or
  provisioning UDIDs.

