# File formats

## Store layout

```text
.protocolith/           (or --store / PROTOCOLITH_STORE)
  ledger.jsonl          the ledger
  lock                  advisory lock file, created on the first write
  cards/                issued cards (default of `issue`)
    PLITH-<protocol_id>-<date>.json
    PLITH-<protocol_id>-<date>.svg
```

Paths are handled with `pathlib`; files are written in binary mode so newlines are always `\n`.

## Ledger line

One [canonical JSON](../concepts/canonical-json.md) object per line, ending with `\n`:

```json
{"body":{},"hash":"64 hex","prev":"64 hex","seq":0,"ts":"2026-11-14T16:00:00Z","type":"freeze","v":1}
```

Exactly these seven keys. A line is at most 1,048,576 bytes without the newline.

## Bodies

Bodies are closed: unknown keys are rejected with `BAD_ENTRY`.

### freeze

| Key | Type | Notes |
| --- | --- | --- |
| `protocol_id` | string | `[A-Za-z0-9][A-Za-z0-9._-]*`, at most 128 characters |
| `version` | string | `[A-Za-z0-9][A-Za-z0-9._+-]*`, at most 64 characters |
| `protocol` | object | must contain the same `protocol_id` and `version` |
| `protocol_sha256` | hash | SHA-256 of the canonical `protocol` |
| `supersedes` | hash or null | hash of the replaced version |

### record

| Key | Type | Notes |
| --- | --- | --- |
| `protocol_sha256` | hash | a protocol frozen at an earlier `seq` |
| `run_id` | non-empty string | |
| `status` | string | one of the [result statuses](../concepts/result-statuses.md) |
| `outcome` | object | free content, no floats |
| `sources` | list of `{id, sha256}` | `id` non-empty, `sha256` a 64-hex hash |
| `reproduction_level` | non-empty string | the card values are listed in [result statuses](../concepts/result-statuses.md) |
| `claim_boundary` | non-empty string | where the claim stops |
| `deviations` | list of integers | `seq` of earlier deviations of the same protocol |
| `block_reason` | string, optional | required for `BLOCKED_SOURCE` |
| `drift_reason` | string, optional | required for `SOURCE_DRIFT` |
| `card` | object, optional | extra evidence-card fields, used by `issue` |

### deviation

`protocol_sha256` (a frozen protocol), `kind` (non-empty string), `description` (non-empty string).

### issue

`record_seq` (integer), `format` (`evidence-card-json-svg`), `card_sha256` (hash).

## Hash

Lowercase 64-character hexadecimal, SHA-256 of the canonical bytes.

## Timestamp

`YYYY-MM-DDTHH:MM:SSZ`, UTC, whole seconds, a valid calendar date and time.

## Card JSON

The canonical bytes of the evidence card, no trailing newline. Fields derived from the record are
`claim_boundary`, `created_at` (the record's `ts`), `evidence_id` (`PLITH-<protocol_id>-<date>`),
`ledger_record_seq`, `protocol_id`, `protocol_sha256`, `protocol_version`, `raw_payload_committed` (always
`false`), `reproduction_level`, `result_status`, `sources`, and `block_reason` or `drift_reason` when present.
Defaults that `card` may override: `last_verified_date`, `record_type` (`evidence_result`), `registry_sequence`
(record `seq` + 1). The remaining fields come from `card`; see [EVIDENCE_CARD](../EVIDENCE_CARD.md).

The normative text is in the [core specification](../spec/CORE_SPEC.md).
