# Error codes

Every error carries a stable machine code. On the CLI the first line on stderr is
`protocolith: CODE: message`, followed by one indented line per rule violation and one `hint (CODE): ...` line with
what to do next where a hint exists; with `--json` a canonical JSON
object is printed on stdout (`ok`, `codes`, `error`, `violations`); `error` also has `hint` when there is one. In Python the codes are `exc.code` and
`exc.codes()`.

## Exit codes

| Exit | Class | Meaning |
| --- | --- | --- |
| 0 | | ok |
| 1 | `VerificationFailed` | the stored ledger does not verify (`verify-ledger`, or any command that has to load a damaged ledger) |
| 2 | `InputError` | bad input or the new entry would break a rule; nothing was written |
| 3 | `EnvError` | I/O or environment error |

## Verification codes (rules R1 to R11 and limits)

| Code | Rule | Meaning |
| --- | --- | --- |
| `BAD_SEQ` | R1 | `seq` is not the expected next number |
| `BAD_PREV` | R2 | `prev` differs from the previous entry's hash |
| `BAD_HASH` | R3 | `hash` (or a protocol hash) does not match the recomputed value |
| `NOT_CANONICAL` | R3 | the line is not the exact canonical form |
| `TS_REGRESSION` | R4 | `ts` is earlier than the previous entry's (also a reason to reject an append) |
| `UNKNOWN_PROTOCOL` | R5 | a record or deviation names a hash not frozen earlier; or `supersedes` names an unknown hash or another protocol |
| `DUPLICATE_FREEZE` | R6 | `(protocol_id, version)` already frozen |
| `BAD_STATUS` | R7 | status not in the closed set |
| `MISSING_FIELD` | R7 | a required field (including a conditional one) is missing or blank |
| `DANGLING_REF` | R8 | a referenced entry is missing, of the wrong type, or belongs to another protocol |
| `BAD_CARD` | R9 | `card_sha256` differs from the card rebuilt from the record |
| `UNKNOWN_VERSION` | R10 | format version `v` is not known |
| `TRUNCATED_TAIL` | R11 | the last line is incomplete |
| `ENTRY_TOO_LARGE` | limit | a line is longer than 1,048,576 bytes |
| `TOO_DEEP` | limit | nesting deeper than 64 |
| `HEAD_MISMATCH` | anchor | `--expect-head`: the entry at `SEQ` is missing or has another hash (exit 1) |
| `BAD_ENTRY` | structure | wrong keys or types; bodies are closed, unknown keys are rejected |
| `ANCHOR_MISMATCH` | anchor | `--anchors`: the entry at an anchored `seq` has another hash: the ledger was rewritten (exit 1) |
| `ANCHOR_AHEAD` | anchor | `--anchors`: the ledger has fewer entries than an anchor says: it was truncated (exit 1) |
| `BAD_DISCLOSURE` | disclosure | `verify-disclosure`: not a disclosure of this version, or a line, a count or the head is wrong (exit 1) |
| `DISCLOSURE_HASH` | disclosure | `verify-disclosure`: a full entry does not hash to its stated hash (exit 1) |
| `DISCLOSURE_CHAIN` | disclosure | `verify-disclosure`: a `prev` is not the hash of the line before: an entry was removed, reordered or replaced (exit 1) |
| `ANCHOR_INVALID` | anchor | `--anchors`: an anchor file, or a stored time-stamp response it lists, is malformed, edited or missing (exit 1) |

After an unparseable line the next `prev` is not checked, to avoid a cascade of reports. In a violation, `seq`
is the zero-based line index.

## Canonicalization and input

| Code | Meaning |
| --- | --- |
| `BAD_JSON` | not valid JSON, or starts with a byte-order mark |
| `BAD_UTF8` | not valid UTF-8 |
| `BAD_TYPE` | a value of a type that is not allowed |
| `FLOAT_NOT_ALLOWED` | a number with a fraction or exponent; write a string |
| `NON_FINITE` | `NaN` or infinity |
| `INT_RANGE` | integer outside +/- (2^53 - 1) |
| `DUPLICATE_KEY` | repeated key in an object |
| `LONE_SURROGATE` | an unpaired surrogate in a string |

## Operations and environment

| Code | Exit | Meaning |
| --- | --- | --- |
| `NO_LEDGER` | 3 | no ledger at the store path (reading a missing ledger is never an empty pass) |
| `NO_PARTIAL_TAIL` | 2 | `repair` found no partial last line |
| `LOCK_TIMEOUT` | 3 | the lock was not obtained within 30 seconds |
| `IO_ERROR` | 3 | an operating-system error, with its class and text |
| `BAD_PATH` | 2 | `capture`: the file is outside the current directory, missing, or not a regular file |
| `BAD_CLOCK` | 2 | the clock value is not `YYYY-MM-DDTHH:MM:SSZ` |
| `CARD_EXISTS` | 2 | the card file exists with different content |
| `CARD_CONFLICT` | 2 | `card` keys contradict values derived from the record |
| `CARD_INVALID` | 2 | the card failed validation for another reason |
| `BAD_POLICY` | 2 | `disclose`, `atlas --policy`: the visibility policy is not valid (`protocolith schema policy`) |
| `ANCHOR_EXISTS` | 2 | `anchor`: an anchor file or statement file of this head exists with other content |
| `EMPTY_LEDGER` | 2 | `anchor`: the ledger has no entries |
| `BAD_URL` | 2 | `anchor`: `--tsa` or `--wayback` is not an http or https URL |
| `NOT_A_GIT_REPO` | 2 | `anchor --git-tag`: the current directory is not inside a git repository |
| `ANCHOR_FAILED` | 3 | `anchor`: a network request, a time-stamp response or a git command failed; the local anchor and the methods that succeeded were kept |
| `VERIFICATION_FAILED` | 1 | the ledger could not be loaded because it does not verify; the violations are attached |

The authoritative list is section 11 of the [core specification](../spec/CORE_SPEC.md).
