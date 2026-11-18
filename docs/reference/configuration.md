# Configuration and environment variables

Protocolith has no configuration file.

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `PROTOCOLITH_STORE` | all ledger commands, Python `resolve_store` | Store directory when `--store` is not given. Default `.protocolith`. |
| `PROTOCOLITH_NOW` | all operations that append | Fixed UTC timestamp `YYYY-MM-DDTHH:MM:SSZ`, for tests and fixtures. An invalid value is `BAD_CLOCK`. The `clock` argument of the Python API takes precedence. |

An empty value counts as unset.

## Command-line options

| Option | Commands | Meaning |
| --- | --- | --- |
| `--store DIR` | all ledger commands and `mcp` | Store directory |
| `--json` | all ledger commands except `mcp` | Canonical JSON on stdout |
| `--expect-head SEQ:HASH` | `verify-ledger` | Also require the entry at `SEQ` to have this hash |
| `--anchors` | `verify-ledger` | Also check every anchor in `<store>/anchors` (`ANCHOR_MISMATCH`, `ANCHOR_AHEAD`, `ANCHOR_INVALID`) |
| `--tsa URL`, `--wayback URL`, `--git-tag`, `--sign`, `--write-head FILE` | `anchor` | Extra anchoring methods and the statement file; nothing networked or git-related happens without them |
| `--seq N` or `--protocol ID` | `claim-check` | Exactly one: the record, or the latest record of a protocol |
| `--supersedes SHA256` | `freeze` | Hash of the version this one replaces |
| `--out DIR` | `issue` | Card directory, default `<store>/cards` |
| `--protocol ID`, `--type TYPE`, `--status STATUS`, `--tail N` | `log` | Filters; `--protocol` also on `summary` |
| `--file PATH` (repeatable), `--env` | `capture` | Files to hash (inside the working directory); include the environment |
| `--truncate-partial-tail` | `repair` | Required; remove the partial last line |
| `--version` | global | Print the installed version |

## Fixed limits

| Limit | Value |
| --- | --- |
| Ledger line | 1,048,576 bytes |
| JSON nesting depth | 64 |
| Integer range | +/- (2^53 - 1) |
| Lock wait | 30 seconds |
| `protocol_id` / `version` length | 128 / 64 characters |

They are constants of the format, not settings.
