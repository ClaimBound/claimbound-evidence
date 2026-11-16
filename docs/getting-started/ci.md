# Using it in CI

The commands are headless and deterministic enough for a pipeline. This page lists what to rely on. The longer
guide is [headless and CI use](../guides/headless-ci.md).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | ok |
| 1 | the stored ledger does not verify |
| 2 | the operation was rejected (bad input, or the new entry would break a rule); nothing was written |
| 3 | I/O or environment error, for example no ledger at the store path, or the lock timed out |

## A minimal verification job

```bash
protocolith verify-ledger --store .protocolith
```

Fails the job with code 1 if any rule R1 to R11 is violated, and with code 3 if the ledger is missing. A
missing ledger is never an empty pass.

## Machine-readable output

Every command except `mcp` accepts `--json` and prints canonical JSON on stdout:

```bash
protocolith verify-ledger --json
```

```json
{"codes":[],"count":3,"head":{"hash":"...","seq":2},"ok":true,"violations":[]}
```

On failure the error text goes to stderr and, with `--json`, a canonical JSON error object goes to stdout.

## Pitfalls

- The clock is the machine clock. Timestamps never decrease within a ledger; an append whose time is earlier
  than the last entry is rejected with `TS_REGRESSION`. Do not append from several machines to a copy of the same
  file.
- The store uses an advisory lock with a 30 s timeout, so parallel jobs on the same file serialise.
- CI is the wrong place to be the only copy of a ledger; keep it as an artifact or in git, and compare the head
  with an anchored value ([anchoring](../guides/anchoring-the-head.md)).
- To detect a removed tail or a replaced ledger, compare with an anchored head:
  `protocolith verify-ledger --expect-head SEQ:HASH` exits with 1 and `HEAD_MISMATCH` if the entry at `SEQ`
  has another hash or does not exist.
