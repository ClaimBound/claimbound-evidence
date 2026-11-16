# Headless and CI use

Protocolith needs no display, no network and no background process. It reads and writes files in the store
directory and prints to stdout and stderr.

## Choosing the store

| Way | Notes |
| --- | --- |
| `--store DIR` | highest priority |
| `PROTOCOLITH_STORE=DIR` | used when `--store` is not given |
| `.protocolith` | default, relative to the working directory |

## Verifying in a pipeline

```bash
protocolith verify-ledger --store ledgers/main --json > verdict.json
echo $?
```

| Exit code | When |
| --- | --- |
| 0 | the ledger verifies |
| 1 | a rule is violated; codes are on stderr and in `verdict.json` (`codes`, `violations`) |
| 3 | no ledger at the path, I/O error, or the lock timed out |

`--json` output is canonical JSON, one object. For `verify-ledger` it has `ok`, `count`, `head` (`hash`, `seq`),
`codes` and `violations` (each with `code`, `seq`, `message`; `seq` is the line index).

## Recording from a job

```bash
protocolith record record.json --store "$STORE" --json
```

Exit 2 means the record was rejected and nothing was written; the JSON on stdout names the codes. A record that
was accepted is not deduplicated: running the same command twice appends two records.

## Concurrency

Appends take an exclusive advisory lock and wait up to 30 seconds (`LOCK_TIMEOUT`, exit 3). Several jobs can
append to one store; they are serialised. Do not append from two machines to copies of one file: timestamps and
sequence numbers would diverge and one copy would fail verification of the merged result.

## Time

The timestamp is the machine clock, whole seconds, UTC. For tests and reproducible fixtures set
`PROTOCOLITH_NOW=2026-11-15T10:00:00Z`; it must have exactly that form, otherwise `BAD_CLOCK`. Do not set it in
real use: a value you choose is exactly as trustworthy as your clock, no more.

## A GitHub Actions sketch

```yaml
- run: uv sync
- run: uv run protocolith verify-ledger --store ledgers/main
```

## What to keep as artifacts

The ledger file, the cards folder, and the output of `protocolith head --json`. The head is what you compare
against an anchored value ([anchoring](anchoring-the-head.md)).

## Checking against an anchored head

```bash
protocolith verify-ledger --expect-head 2:7e991c8d63f3f661894015c450b41cdb3809af305af4f562f8224466314eecd7
```

Passes only if the ledger verifies and the entry at that `seq` has that hash. Otherwise exit 1 with
`HEAD_MISMATCH`. A malformed `SEQ:HASH` value is exit 2.
