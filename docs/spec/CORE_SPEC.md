# Protocolith Core Specification

Status: draft 0.1 (target: Protocolith 0.6.0). This document defines the core. The reference
implementation is the `protocolith.core` package; any other implementation must pass the
conformance vectors in `spec/vectors/` to claim compatibility.

## 1. Scope

Protocolith does exactly one thing: it **records, verifies and issues trial records**.

1. **Freeze** a protocol before a run.
2. **Record** the outcome of a run against a frozen protocol.
3. **Verify** that the history is intact and every record follows its frozen protocol.
4. **Issue** a human-readable card from a verified record.

Non-goals: running experiments, fetching data, scheduling, storing raw payloads, judging whether a
protocol is scientifically good, answering questionnaires. The core uses only the Python standard library.

## 2. Canonical JSON (PCJ-1)

All hashes are computed over canonical bytes.

- UTF-8, no byte-order mark, no insignificant whitespace, no trailing newline in the hashed bytes.
- Objects: keys unique, sorted by Unicode code point; duplicate keys in input are an error.
- Allowed values: object, array, string, boolean, null, integer in `[-(2^53-1), 2^53-1]`.
- **Floats are not allowed.** Write decimals as strings (`"0.001"`). This keeps hashes identical in every language.
- Strings: any Unicode except lone surrogates; escapes are `\"` `\\` `\b` `\f` `\n` `\r` `\t` and `\u00XX` for other
  controls below U+0020; everything else is written literally.
- `NaN`, `Infinity`, and non-finite numbers are errors.

`sha256(x)` is the lowercase 64-hex SHA-256 of the PCJ-1 bytes of `x`.

## 3. Ledger

A ledger is a UTF-8 text file with one entry per line (`\n` terminated). Each line is the PCJ-1 form of:

```json
{"body":{...},"hash":"<64 hex>","prev":"<64 hex>","seq":0,"ts":"2026-11-14T16:00:00Z","type":"freeze","v":1}
```

- `v`: format version, integer, `1` for this document.
- `seq`: integer, starts at 0, increases by exactly 1.
- `ts`: UTC time `YYYY-MM-DDTHH:MM:SSZ`, whole seconds.
- `prev`: `hash` of the previous entry; 64 zeros for `seq` 0.
- `hash`: `sha256` of the entry object **without** the `hash` field.
- `type`: `freeze`, `record`, `deviation` or `issue`.

### 3.1 Bodies

| type | body fields |
| --- | --- |
| `freeze` | `protocol_id`, `version`, `protocol` (object), `protocol_sha256` (= `sha256(protocol)`), `supersedes` (hash or null) |
| `record` | `protocol_sha256`, `run_id`, `status`, `outcome` (object), `sources` (list of `{id, sha256}`), `reproduction_level`, `claim_boundary`, `deviations` (list of `seq`), optional `block_reason`, `drift_reason` |
| `deviation` | `protocol_sha256`, `kind`, `description` |
| `issue` | `record_seq`, `format`, `card_sha256` |

`status` is one of the closed set of result statuses of the evidence-card format: `PASSED_UNDER_PROTOCOL`,
`NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE`, `SOURCE_DRIFT`, `REPRODUCED_OUTCOME`.
`BLOCKED_SOURCE` requires `block_reason`; `SOURCE_DRIFT` requires `drift_reason`. `PASSED_UNDER_PROTOCOL`,
`NEGATIVE_RESULT_UNDER_PROTOCOL` and `REPRODUCED_OUTCOME` require a non-empty `sources` list (code `MISSING_FIELD`).
Absence of evidence is never recorded as `NEGATIVE_RESULT_UNDER_PROTOCOL`; use `BLOCKED_SOURCE` or `INSUFFICIENT_COVERAGE`.

### 3.2 Rules

| Rule | Statement | Code on violation |
| --- | --- | --- |
| R1 | `seq` is contiguous from 0 | `BAD_SEQ` |
| R2 | `prev` equals the previous entry's `hash` | `BAD_PREV` |
| R3 | `hash` matches the recomputed value; the line is exactly canonical | `BAD_HASH`, `NOT_CANONICAL` |
| R4 | `ts` never decreases | `TS_REGRESSION` |
| R5 | a `record` names a `protocol_sha256` frozen at an earlier `seq` | `UNKNOWN_PROTOCOL` |
| R6 | one `(protocol_id, version)` is frozen once; its hash never changes | `DUPLICATE_FREEZE` |
| R7 | `status` is in the closed set; conditional fields present | `BAD_STATUS`, `MISSING_FIELD` |
| R8 | every `deviations` seq and `issue.record_seq` points to an earlier entry of the right type | `DANGLING_REF` |
| R9 | `issue.card_sha256` equals the hash of the card re-rendered from the record | `BAD_CARD` |
| R10 | `v` is known | `UNKNOWN_VERSION` |
| R11 | the last line is complete (ends with `\n`, parses) | `TRUNCATED_TAIL` |

A changed protocol is a **new version**: freeze again with `supersedes` set to the old hash. Records always keep
pointing at the hash they were run under.

### 3.3 What the ledger does and does not prove

A valid ledger proves internal consistency and ordering. It does not prove wall-clock time and cannot detect that a
whole ledger was replaced or that its tail was removed. `head` (the last `hash` plus `seq`) may be published or
anchored elsewhere (a signed git tag, a timestamp service); a later check against that head detects removal (`verify-ledger --expect-head SEQ:HASH`; a mismatch yields `HEAD_MISMATCH`, exit 1).

## 4. Local store

Default directory: `.protocolith/` in the working directory (override: `--store` or `PROTOCOLITH_STORE`).

- `ledger.jsonl`: the ledger.
- `lock`: advisory lock file; appends take an exclusive lock (`fcntl` on POSIX, `msvcrt` on Windows).
- Append is `write` + `flush` + `fsync` of one complete line; a crash leaves at most one partial last line, which
  `verify` reports as `TRUNCATED_TAIL` and which only an explicit `repair --truncate-partial-tail` removes.
- All paths are handled with `pathlib`; newlines are always `\n` (files opened in binary mode).
- The clock is injectable (`PROTOCOLITH_NOW` for tests); timestamps are UTC.

## 5. Interfaces

All three expose the same operations with the same semantics.

| Operation | CLI | Python | MCP tool |
| --- | --- | --- | --- |
| freeze | `protocolith freeze FILE` | `core.freeze(store, protocol)` | `protocolith_freeze` |
| record | `protocolith record FILE` | `core.record(store, body)` | `protocolith_record` |
| deviation | `protocolith deviation FILE` | `core.deviation(store, body)` | `protocolith_deviation` |
| verify | `protocolith verify-ledger` | `core.verify(store)` | `protocolith_verify` |
| issue | `protocolith issue SEQ` | `core.issue(store, seq)` | `protocolith_issue` |
| log / head | `protocolith log`, `protocolith head` | `core.entries(store)`, `core.head(store)` | `protocolith_log` |

CLI exit codes: `0` ok; `1` the stored ledger does not verify (codes on stderr and, with `--json`, on stdout);
`2` the operation was rejected (bad input, or the new entry would break a rule, including `TS_REGRESSION`) and nothing was written;
`3` I/O or environment error (missing ledger, lock timeout). `--json` output is PCJ-1. Reading a missing ledger is `NO_LEDGER`
(exit 3), never an empty pass.

The MCP server speaks stdio JSON-RPC with `initialize`, `tools/list` and `tools/call`, uses no network and no
third-party package, and never writes outside the store.

## 6. Conformance vectors

`spec/vectors/` holds language-neutral JSON files: canonicalization cases (input text, expected bytes or error),
hash cases, and ledgers (each with the expected verdict and codes). Every rule R1 to R11 has at least one failing vector.
A change to the vectors is a change to the specification and needs a version bump.

## 7. Versioning

The ledger format version `v` changes only on incompatible changes. The core API follows semantic versioning from 1.0.
Version 1.0.0 additionally requires an independent external rerun and a second implementation that passes the vectors.

## 8. Relation to evidence cards

An `issue` entry renders the existing evidence-card JSON and SVG from a verified record, so the registry, validator and
static views keep working. Cards created before this specification stay valid under the card validator and are mapped to
their current ids by `docs/MIGRATION_ID_MAP.json`.

## 9. Limits

- One ledger line is at most `MAX_ENTRY_BYTES = 1,048,576` bytes (without the newline). A longer line is not parsed
  (`ENTRY_TOO_LARGE`).
- JSON nesting depth is at most 64, counting the top-level container as 1 (`TOO_DEEP`).
- `protocol_id` (at most 128 characters) and `version` (at most 64 characters) are filename-safe: `[A-Za-z0-9][A-Za-z0-9._+-]*` (`+` is allowed in `version` only).
- Lock waits time out after 30 seconds (`LOCK_TIMEOUT`).

## 10. Issuing cards

`record.body` may hold an optional `card` object with extra evidence-card fields (operator, source name and URL, domain,
claim type, and so on). `issue` builds the card from the record, the frozen protocol and `card`, validates it with the
evidence-card validator and renders JSON and SVG.

- `evidence_id` is `PLITH-<protocol_id>-<date of the record>`; `registry_sequence` defaults to the record `seq` + 1.
- A `card` key that contradicts a value derived from the record is `CARD_CONFLICT`; missing required card fields are
  `MISSING_FIELD` and are named; any other validator failure is `CARD_INVALID`.
- The card file is the PCJ-1 bytes of the card with no trailing newline, so the file's SHA-256 equals `card_sha256`.
- Issuing twice writes the same bytes; if the file exists with different content the result is `CARD_EXISTS`.
- `raw_payload_committed` is always false.

## 11. Error codes

Verification: `BAD_SEQ`, `BAD_PREV`, `BAD_HASH`, `NOT_CANONICAL`, `TS_REGRESSION`, `UNKNOWN_PROTOCOL`, `DUPLICATE_FREEZE`,
`BAD_STATUS`, `MISSING_FIELD`, `DANGLING_REF`, `BAD_CARD`, `UNKNOWN_VERSION`, `TRUNCATED_TAIL`, `ENTRY_TOO_LARGE`, `TOO_DEEP`,
`BAD_ENTRY` (structure or type problem; bodies are closed, so unknown keys are rejected), `HEAD_MISMATCH` (`--expect-head` check failed).

Canonicalization and input: `BAD_JSON` (including a byte-order mark), `BAD_UTF8`, `BAD_TYPE`, `FLOAT_NOT_ALLOWED`, `NON_FINITE`,
`INT_RANGE`, `DUPLICATE_KEY`, `LONE_SURROGATE`.

Operations and environment: `NO_LEDGER`, `NO_PARTIAL_TAIL`, `LOCK_TIMEOUT`, `IO_ERROR`, `BAD_CLOCK`, `CARD_EXISTS`, `CARD_CONFLICT`,
`CARD_INVALID`, `VERIFICATION_FAILED`.

Chain checks: `prev` is compared with the stored `hash` of the previous line, so tampering shows as `BAD_HASH` on that line only;
after an unparseable line the next `prev` is not checked, to avoid cascades. `supersedes` must name an earlier freeze of the same
`protocol_id`; a referenced deviation must belong to the same protocol and be listed in the record's `deviations`.

`repair --truncate-partial-tail` removes only an unterminated last line and refuses if the rest does not verify.

## 12. Coverage note

The reference implementation is held at 100% line and branch coverage of `protocolith.core`. The two platform-specific lock
modules are marked `# pragma: no cover` as a whole because each runs only on its own platform; both are exercised in CI.
