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
Section 13 defines anchor statements and anchor files, which make this check systematic (`verify-ledger --anchors`).

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
| verify | `protocolith verify-ledger [--expect-head SEQ:HASH] [--anchors]` | `core.verify(store, expect_head=None, anchors=False)` | `protocolith_verify` (`expect_head`, `anchors`) |
| issue | `protocolith issue SEQ` | `core.issue(store, seq)` | `protocolith_issue` |
| log / head | `protocolith log`, `protocolith head` | `core.entries(store)`, `core.log(store, ...)`, `core.head(store)` | `protocolith_log` |
| show | `protocolith show SEQ` | `core.show(store, seq)` | `protocolith_show` |
| summary | `protocolith summary [--protocol ID]` | `core.summary(store, protocol=None)` | `protocolith_summary` |
| capture | `protocolith capture [--file PATH ...] [--env]` | `core.capture(files, env=False)` | `protocolith_capture` |
| schema | `protocolith schema [NAME]` | `core.schema_for(name)` | `protocolith_schema` |
| atlas | `protocolith atlas [--store DIR] [--cards DIR ...] [--out FILE_OR_DIR]` | `core.build_atlas(...)` | `protocolith_atlas` |
| anchor | `protocolith anchor [--tsa URL] [--wayback URL] [--git-tag [--sign]] [--write-head FILE]` | `core.anchor_head(store, ...)` | `protocolith_anchor` (local anchor and optional `tsa` only) |
| claim check | `protocolith claim-check --seq N \| --protocol ID` | `core.claim_check(store, seq=N)` or `protocol=ID` | `protocolith_claim_check` |
| init | `protocolith init` | `core.init(store)` | |

CLI exit codes: `0` ok; `1` the stored ledger does not verify (codes on stderr and, with `--json`, on stdout);
`2` the operation was rejected (bad input, or the new entry would break a rule, including `TS_REGRESSION`) and nothing was written;
`3` I/O or environment error (missing ledger, lock timeout). `--json` output is PCJ-1. Reading a missing ledger is `NO_LEDGER`
(exit 3), never an empty pass.

The MCP server speaks stdio JSON-RPC with `initialize`, `tools/list`, `tools/call`, `resources/list`, `resources/read`,
`prompts/list` and `prompts/get`, and uses no third-party package. `initialize` advertises `tools`, `resources` and `prompts`.
It makes a network request only when `protocolith_anchor` is called with `tsa`, and never writes outside the store, except the
one atlas page of `protocolith_atlas` inside the working directory. The prompt `research-agent-protocol` (no arguments) holds
fixed instructions for an AI agent: freeze before any run, record every run including failures and blocked sources, call
`claim_check` before stating a result and use its `may_say` wording, then verify and anchor and report the `anchor_id`.
An unknown prompt name is JSON-RPC error `-32602`.

### 5.1 Read commands

- `log` accepts the filters `protocol` (a `protocol_id`; an unknown one is `UNKNOWN_PROTOCOL`), `type` (an entry type),
  `status` (only records with that result status; a value outside the closed set is `BAD_STATUS`) and `tail` (an
  integer of at least 1: keep the last N matches). Filters combine with AND and keep ledger order.
- `show SEQ` returns the entry, its protocol (`protocol_id`, `version`, `protocol_sha256`, `freeze_seq`; an `issue`
  entry has the protocol of its record), `points_at` (the `deviations` of a record, or the `record_seq` of an issue) and
  `pointed_by` (the entries that point at it). An unknown `seq` is `DANGLING_REF`.
- `summary` returns, as one object: `ok`, `head` (`count`, `hash`, `seq`), `entries_by_type`, `records_by_status`,
  `protocols` (one row per `protocol_id`: `versions`, `latest_version`, `records`, `latest_status`, `deviations`,
  `cards`) and `problems` (the violations, each `code`, `seq`, `message`). Unlike other reads it does not fail when the
  ledger does not verify: `ok` is false and `problems` says why (CLI exit 1, MCP `isError`). Entries whose protocol was
  never frozen are not tabulated. `--protocol` limits the table and the counts to one protocol. It also holds
  `anchors` (`count` of anchor files and `last_seq`, the highest anchored `seq` that matches the ledger, or null);
  anchor problems (section 13) are added to `problems` and make `ok` false.
- `init` creates the store with an empty ledger; repeating it changes nothing. An empty ledger verifies.

### 5.2 Capture

`capture` returns `{"environment": {"machine", "platform", "protocolith", "python"}, "inputs": [{"path", "sha256", "size"}]}`
to be pasted into the free-form `outcome` of a record. `inputs` lists each named file with its path relative to the
working directory (`/` separators), size in bytes and sha256. `environment` is included with `--env` and whenever no
file is named. It executes nothing and reads no environment variable values. A file outside the working directory (after
resolving links), a missing file or a non-regular file is `BAD_PATH`. The MCP tool takes `files` and `env`.

### 5.3 Schemas and MCP resources

`schema` prints JSON Schema (draft 2020-12) for `freeze` (the protocol object), `record`, `deviation`, `issue` (the input
`{"seq": n}`) and `entry` (the ledger line; `$defs` hold the stored body of each type), or `all`. The schemas are
generated from the same field rules the verifier uses, so they cannot drift from it; conditional requirements
(`block_reason`, `drift_reason`, non-empty `sources`) are included. A schema cannot express every rule (references
between entries, hashes, ordering); the verifier is authoritative.

The MCP server lists and reads these read-only resources (`mimeType` `application/json`): `protocolith://summary`,
`protocolith://ledger` (all entries and the head) and `protocolith://schema/<name>` for each schema name above except
`all`. An unknown URI is JSON-RPC error `-32002`; a failure such as `NO_LEDGER` is `-32000` with the code in the message.

### 5.4 Error hints

An error may carry a one-line `hint`: printed as `hint (CODE): ...` on stderr and, in JSON, as `error.hint`. Hints are
advice, not part of the contract; codes and exit codes are.

### 5.5 Atlas

`atlas` writes one self-contained HTML file (default `protocolith-atlas.html`; `--out` is a `.html` file or a directory).
Sources: a ledger (`--store`, verified like `verify-ledger`; only `record` entries become rows, with the card derived as for
`issue`) and/or evidence card JSON files found recursively under each `--cards DIR`. With neither option a local
ledger is used, else `docs/evidence_cards`. A file that is not valid UTF-8 JSON, not an object, larger than 2 MiB, or lacking
a string `evidence_id` and `result_status` is skipped and counted (`issues`); unknown fields are kept. Equal
`evidence_id` values keep the first record. Cards read from files are not verified against any ledger.

- **Failure semantics.** A ledger that does not verify still produces the atlas, with a red integrity banner and the
  problems; the command exits `1`. Other errors keep the usual codes (`2` input, `3` environment); nothing is written then.
- **Page.** Inline CSS and JavaScript, the data as `<script type="application/json" id="atlas-data">`, no network request,
  no external font or library, a Content-Security-Policy meta element that forbids connections. The JSON is ASCII with `<`,
  `>` and `&` written as `\u` escapes, so no content can end the script block. The script writes data with `textContent`
  and DOM calls only. The same input gives the same bytes; the page holds no wall-clock value.
- **Data size.** A row holds the evidence id, protocol, status, domain, reproduction level, date, claim boundary, hash and
  a source text; every other field travels deflate-compressed in blocks of 128 records and is decoded when a record is
  opened (a browser without `DecompressionStream` shows the row fields only). Strings are clipped at 2000 characters,
  lists at 100 items and nesting at 8 levels. `--max-rows N` embeds only the newest N records; totals stay complete.
- **Statuses.** The six statuses of this specification have a letter and a symbol in addition to a colour; any other
  status is displayed as found and never hidden or reclassified.
- **Languages.** `atlas_i18n/en.json` is the English catalog (every visible string has a key). `--i18n DIR` adds every
  `<code>.json` (`{"_name": "Native name", "key": "text"}`); unknown keys and non-string values are ignored with a warning,
  empty values and missing keys fall back to English, and the language switcher appears only when one is present.
  `--default-lang` must name an available language (`BAD_LANG`). No translation ships in the package.

## 6. Conformance vectors

`spec/vectors/` holds language-neutral JSON files: canonicalization cases (input text, expected bytes or error),
hash cases, ledgers (each with the expected verdict and codes), expected-head cases and anchor statements. Every rule R1 to R11 has at least one failing vector.
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

- `evidence_id` is `PLITH-<protocol_id>-<date of the record>-<seq>`, where `seq` is the ledger `seq` of the record as six
  digits (more if needed), so two records of one protocol on one day each get their own card; `registry_sequence` defaults
  to the record `seq` + 1.
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

Anchors (section 13): `ANCHOR_MISMATCH` (an anchored entry is not the one in the ledger: the ledger was rewritten),
`ANCHOR_AHEAD` (the ledger is shorter than an anchor: truncated), `ANCHOR_INVALID` (an anchor file or a stored time-stamp
response is malformed, edited or missing) are verification codes of `verify-ledger --anchors` (exit 1). `ANCHOR_EXISTS`
(an anchor of this head exists with other content, exit 2), `EMPTY_LEDGER` (nothing to anchor, exit 2), `BAD_URL` (exit 2),
`NOT_A_GIT_REPO` (exit 2) and `ANCHOR_FAILED` (a network, time-stamp or git step failed, exit 3) belong to `anchor`.

Operations and environment: `BAD_PATH`, `NO_LEDGER`, `NO_PARTIAL_TAIL`, `LOCK_TIMEOUT`, `IO_ERROR`, `BAD_CLOCK`, `CARD_EXISTS`, `CARD_CONFLICT`,
`CARD_INVALID`, `VERIFICATION_FAILED`.

Chain checks: `prev` is compared with the stored `hash` of the previous line, so tampering shows as `BAD_HASH` on that line only;
after an unparseable line the next `prev` is not checked, to avoid cascades. `supersedes` must name an earlier freeze of the same
`protocol_id`; a referenced deviation must belong to the same protocol and be listed in the record's `deviations`.

`repair --truncate-partial-tail` removes only an unterminated last line and refuses if the rest does not verify.

## 12. Coverage note

The reference implementation is held at 100% line and branch coverage of `protocolith.core`. The two platform-specific lock
modules are marked `# pragma: no cover` as a whole because each runs only on its own platform; both are exercised in CI.

## 13. Anchors

The ledger is self-attested: whoever can write the file can rewrite the whole hash chain consistently, and `verify-ledger`
passes. An anchor ties the head to something the writer cannot change alone.

**Statement.** The PCJ-1 canonical JSON of `{"v": 1, "kind": "protocolith-anchor", "head_seq": N, "head_hash": H, "entries": N+1,
"protocolith_version": V, "created_at": T}` (`created_at` comes from the injected clock; `protocolith_version` is the installed
version or `unknown`). `anchor_id` is the lowercase hex sha256 of those bytes. Vectors: `spec/vectors/anchors.json`.

**Files.** Anchoring writes into `<store>/anchors/` (atomic write through a temporary file, then rename):

- `<seq>-<hash12>.json`: PCJ-1 of `{"anchor_id", "methods": [...], "statement": {...}}` (`hash12` is the first 12 characters of
  the head hash). The statement and `anchor_id` never change: anchoring the same head again reuses the file; only `methods`
  grows, and an equal method is not added twice. A file of the same name that is not an anchor of this head is `ANCHOR_EXISTS`.
- `<seq>-<hash12>.statement`: exactly the statement bytes (no trailing newline), written once; different content is `ANCHOR_EXISTS`.
- `<anchor_id>.tsr`: a stored RFC 3161 response, written once; a different response from another authority is stored as
  `<anchor_id>.<hash12 of the response>.tsr`. A response is never overwritten.

Anchoring requires a ledger that verifies (else `VerificationFailed`) and at least one entry (`EMPTY_LEDGER`). Nothing
networked or git-related happens unless its option is given; the default `anchor` is local. The network and the git program
are reached through injectable callables, so the core is tested without either.

**Methods** (entries of `methods`; every extra option adds one):

| Option | Method | What is recorded |
| --- | --- | --- |
| `--tsa URL` | `rfc3161` | `url`, `file` (the `.tsr` name), `tsr_sha256`, `gen_time` |
| `--wayback URL` | `wayback` | `url` (where you published the statement), `snapshot` (a URL on `web.archive.org`) |
| `--git-tag [--sign]` | `git-tag` | `tag` (`anchor/<seq>-<hash12>`), `signed` |

- *RFC 3161.* A DER TimeStampReq (version 1, SHA-256 imprint of the statement bytes, random 64-bit nonce, `certReq` true) is
  POSTed with content type `application/timestamp-query` (timeout 30 s, response at most 1 MiB). The response must have PKIStatus
  0 or 1 and a message imprint equal to the statement hash; `genTime` is recorded. The core does **not** verify the
  time-stamp signature or the certificate chain. Verify offline with
  `openssl ts -verify -in ID.tsr -data SEQ-HASH12.statement -CAfile CA.pem -untrusted TSA-CERT.pem`; the output of `anchor` prints this command.
- *Wayback.* `GET https://web.archive.org/save/<URL>`; the snapshot is taken from the `Content-Location` or `Location`
  response header and must be on the archive host. It is evidence only if `URL` served exactly the statement (publish the file
  written by `--write-head` first); compare the snapshot with the statement hash yourself.
- *Git tag.* `git tag -a|-s anchor/<seq>-<hash12> -m <statement>` in the current repository, as a fixed argument list, after
  `git rev-parse --is-inside-work-tree` (`NOT_A_GIT_REPO` otherwise). It never pushes; the output prints `git push origin <tag>`.
- Methods are tried in the order tsa, wayback, git tag. If one fails, the methods that succeeded earlier are kept in the anchor
  file and the failure is raised (`ANCHOR_FAILED`, exit 3).
- `--write-head FILE` writes the statement bytes to `FILE` (atomic replace) so that it can be committed, attached to a release,
  uploaded or archived. The MCP tool offers only the local anchor and `tsa`: no git, no arbitrary file write.

**Verification.** `verify-ledger --anchors` (Python `verify(store, anchors=True)`, MCP `protocolith_verify` with `anchors`; also
`core.verify_anchors(store)`) reads every `*.json` file in `anchors/` and reports, with `seq` = the anchored `head_seq`:

- `ANCHOR_INVALID`: the file is unreadable, not valid JSON, not an anchor file, `sha256(canonical statement)` differs from
  `anchor_id`, `entries` differs from `head_seq + 1`, or a listed `rfc3161` response file is missing or does not hash to
  `tsr_sha256` (the `file` must be a plain name without a path separator).
- `ANCHOR_AHEAD`: the ledger has `head_seq` or fewer entries (it was truncated).
- `ANCHOR_MISMATCH`: the ledger has an entry at `head_seq` but its hash differs from `head_hash` (the ledger was rewritten).

Any of these makes the verdict fail (exit 1). A longer ledger whose anchored prefix is unchanged passes. An attacker with write
access to the store can also edit or delete the local anchor files; what resists this is a copy outside the store (the
published statement, the time-stamp, the archive copy, the pushed tag), compared with `verify-ledger --expect-head`
or by hash. A time-stamp proves the statement existed at time T, not that the analysis was planned before T.

## 14. Claim check

`claim_check` answers, from the ledger alone, what may be said about a record. Give exactly one of `seq` (a record) or `protocol`
(the latest record of that `protocol_id`; an unknown one is `UNKNOWN_PROTOCOL`); a `seq` that is not a record is `DANGLING_REF`;
a ledger that does not verify raises `VerificationFailed`. The result is a JSON object with:

| Field | Meaning |
| --- | --- |
| `supported` | true when the status is `PASSED_UNDER_PROTOCOL`, `NEGATIVE_RESULT_UNDER_PROTOCOL` or `REPRODUCED_OUTCOME` |
| `status`, `claim_boundary`, `seq` | as recorded |
| `protocol_id`, `protocol_version`, `protocol_sha256` | the frozen protocol the record names |
| `sources` | the record sources, `id` and `sha256` |
| `protocol_frozen_before_record` | the `ts` of the freeze is strictly earlier than the `ts` of the record (timestamps have a resolution of one second, so equal is not shown to be earlier) |
| `deviations` | the number of deviations listed in the record |
| `anchored` | the record `seq` is at most the highest `head_seq` of an anchor that matches the ledger |
| `independent_reproduction` | a `REPRODUCED_OUTCOME` record exists for the same `protocol_sha256` |
| `may_say` | one sentence built from fixed templates: protocol id and version, run id, a phrase for the status, and the boundary |
| `must_not_say` | phrases the ledger does not support, in this order when they apply: `independently reproduced` (no reproduction), `negative result` and `positive result` (status is `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE` or `SOURCE_DRIFT`), `prospective` and `preregistered` (not frozen before the record), `externally anchored` (not anchored), `followed the protocol without deviations` (deviations), and always `applies beyond the claim boundary` |

A protocol with no record yields `supported` false, `seq` null, `may_say` saying that no result is recorded, and `must_not_say`
`["any result", "passed", "failed", "reproduced"]`. The output is deterministic and contains no text beyond these templates, the
recorded values and the claim boundary text as written by the recorder. `claim_check` limits what an agent can honestly
report; it does not check that the analysis itself was sound.
