# Roadmap

This page covers the core ledger. The earlier plan for the evidence-card toolkit is in
[Roadmap 2026](../ROADMAP_2026.md) and [planned work not shipped](../PLANNED_NOT_SHIPPED.md); both describe the
pre-rename project and keep their original status wording.

## Implemented on the development branch

- Canonical JSON (PCJ-1), the hash-chained ledger with rules R1 to R11, the local store with locking and durable
  append.
- Commands `freeze`, `record`, `deviation`, `verify-ledger`, `issue`, `log`, `head`, `repair` and `mcp`, with the
  Python API and the MCP server.
- Card issuing from a verified record (JSON and SVG).
- `verify-ledger --expect-head SEQ:HASH`, which compares the ledger with an anchored head (`HEAD_MISMATCH`).
- The [core specification](../spec/CORE_SPEC.md) (draft 0.1) and the
  [conformance vectors](../reference/conformance-vectors.md).
- 100% line and branch coverage of `protocolith.core` ([testing](../development/testing.md)).

## Planned

| Item | Target | Notes |
| --- | --- | --- |
| Release 0.6.0 with `pip install protocolith` | 0.6.0 | Released 2026-11-16. |
| Release 0.7.0: anchoring, claim-check, selective disclosure | 0.7.0 | In preparation. |
| conda-forge package | no date | Submitted; waiting for review. |
| A second implementation that passes the vectors | before 1.0.0 | None exists. |
| An independent external rerun of a recorded run | before 1.0.0 | None has been reported. |

Version 1.0.0 is reserved until the last two items exist. Everything marked planned here is not implemented.

## Not planned

Running experiments, fetching data, scheduling, storing raw payloads, judging whether a protocol is good, and
hosting a service. These are non-goals of the core.
