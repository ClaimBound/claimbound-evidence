# Ledger and hash chain

The ledger is a UTF-8 text file, `.protocolith/ledger.jsonl`, with one entry per line. Each line is the
[canonical JSON](canonical-json.md) form of one entry followed by `\n`:

```json
{"body":{...},"hash":"<64 hex>","prev":"<64 hex>","seq":0,"ts":"2026-11-14T16:00:00Z","type":"freeze","v":1}
```

| Field | Meaning |
| --- | --- |
| `v` | Format version, `1`. |
| `seq` | 0, 1, 2, ... without gaps. |
| `ts` | UTC time of the append, whole seconds, `YYYY-MM-DDTHH:MM:SSZ`. |
| `prev` | The `hash` of the previous entry; 64 zeros for `seq` 0. |
| `hash` | SHA-256 of the entry without its `hash` field. |
| `type` | `freeze`, `record`, `deviation` or `issue`. |
| `body` | Depends on the type; closed set of keys. See [file formats](../reference/file-formats.md). |

## Why a chain

Because each entry contains the hash of the one before and its own hash covers `prev`, changing any byte in an
earlier line changes its hash and breaks the `prev` link of the next line. Inserting, deleting or reordering
entries breaks the chain in the same way. Verification recomputes everything from the bytes.

## What verification checks

| Rule | Statement | Code |
| --- | --- | --- |
| R1 | `seq` is contiguous from 0 | `BAD_SEQ` |
| R2 | `prev` equals the previous entry's hash | `BAD_PREV` |
| R3 | `hash` matches; the line is exactly canonical | `BAD_HASH`, `NOT_CANONICAL` |
| R4 | `ts` never decreases | `TS_REGRESSION` |
| R5 | a record names a protocol frozen at an earlier `seq` | `UNKNOWN_PROTOCOL` |
| R6 | one `(protocol_id, version)` is frozen once | `DUPLICATE_FREEZE` |
| R7 | status is in the closed set; conditional fields present | `BAD_STATUS`, `MISSING_FIELD` |
| R8 | references (`deviations`, `record_seq`) point to earlier entries of the right type | `DANGLING_REF` |
| R9 | `card_sha256` equals the hash of the card re-rendered from the record | `BAD_CARD` |
| R10 | `v` is known | `UNKNOWN_VERSION` |
| R11 | the last line is complete | `TRUNCATED_TAIL` |

Also checked: entry size (`ENTRY_TOO_LARGE`), nesting depth (`TOO_DEEP`) and the closed shape of each body
(`BAD_ENTRY`). Full list: [error codes](../reference/error-codes.md).

Writes are checked too. Before a new line is appended, Protocolith stages it and runs the same rules; if the new
entry would break one, it is rejected and nothing is written.

## Appending

An append takes an exclusive lock, writes one complete line, flushes and calls `fsync`. A crash can leave at
most one partial last line; see [repair and crash recovery](../guides/repair-and-crash-recovery.md).

## What the ledger proves and does not

- A valid ledger proves **internal consistency and ordering**: every entry follows the rules, and nothing was
  changed, removed from the middle or reordered without breaking the chain.
- It does **not** prove wall-clock time. `ts` is whatever the appending machine's clock said; only its
  monotonicity is checked.
- It cannot detect that a **whole ledger was replaced** by another valid one, or that its **tail was removed**.
  For that, publish the head somewhere you do not control alone and check against it with
  `verify-ledger --expect-head`; see [anchoring the head](../guides/anchoring-the-head.md).
- It says nothing about whether the data is true or the protocol sound.
