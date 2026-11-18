# MCP tools and resources

Reference for `protocolith mcp`. For setup and an example session see
[Use Protocolith from an AI agent](../guides/ai-agent-mcp.md).

Transport: newline-delimited JSON-RPC 2.0 on stdio. Methods: `initialize`, `ping`, `tools/list`, `tools/call`,
`resources/list`, `resources/read`, `prompts/list`, `prompts/get`. `initialize` advertises `tools`, `resources` and `prompts`. The server answers with the protocol version the client asks for if it knows it
(`2025-06-18`, `2025-03-26`, `2024-11-05`), otherwise the newest. Notifications get no answer. Unknown methods return
`-32601`; malformed input `-32700` or `-32600`.

## Tools

Arguments not listed are rejected (`additionalProperties` is false). A result is one text content item holding
canonical JSON. `isError` is true when the operation was rejected or the ledger does not verify; the JSON then carries
`ok: false`, `codes`, `error` (with a `hint` where there is one) and `violations`, exactly as with `--json`.

| Tool | Arguments | Same as |
| --- | --- | --- |
| `protocolith_summary` | optional `protocol` | `protocolith summary`: verdict, head, counts, per-protocol table, problems. Start here. |
| `protocolith_log` | optional `protocol`, `type`, `status`, `tail` | `protocolith log` plus the head |
| `protocolith_show` | `seq` (integer, at least 0) | `protocolith show` |
| `protocolith_schema` | optional `name` (`freeze`, `record`, `deviation`, `issue`, `entry`, `all`) | `protocolith schema` |
| `protocolith_capture` | optional `files` (paths inside the working directory), `env` | `protocolith capture` |
| `protocolith_atlas` | optional `out`, `title`, `cards` (directories), `i18n`, `default_lang`, `max_rows` | `protocolith atlas`; returns the path written |
| `protocolith_freeze` | `protocol` (object), optional `supersedes` | `protocolith freeze` |
| `protocolith_record` | `body` (object) | `protocolith record` |
| `protocolith_deviation` | `body` (object) | `protocolith deviation` |
| `protocolith_verify` | optional `expect_head` (`SEQ:HASH`), `anchors` (boolean) | `protocolith verify-ledger [--expect-head] [--anchors]` |
| `protocolith_claim_check` | `seq` or `protocol` (exactly one) | `protocolith claim-check`: what may and may not be said about a record. Call it before stating any result. |
| `protocolith_anchor` | optional `tsa` (URL) | `protocolith anchor [--tsa URL]`: the local anchor, plus an RFC 3161 time-stamp when `tsa` is given |
| `protocolith_issue` | `seq` (integer, at least 0) | `protocolith issue` |

`protocolith_issue` writes cards inside the store (`<store>/cards`); there is no output directory argument.
`protocolith_capture` refuses paths that leave the server's working directory (`BAD_PATH`), runs nothing and reads no
environment values. Only the freeze, record, deviation and issue tools write to the store.
`protocolith_atlas` writes one HTML page and nothing else: `out` (default `protocolith-atlas.html`), `cards` and `i18n`
must stay inside the working directory (`BAD_PATH`). Without `cards` it uses the server's ledger; `isError` is true
when the ledger does not verify (the page is still written, with a warning banner).

`protocolith_anchor` writes into `<store>/anchors` and, only when `tsa` is given, sends one HTTP POST to that URL (the
time-stamp signature is not verified by Protocolith; the result lists the `openssl ts -verify` command). It offers no git and no
file output; use the CLI for `--git-tag`, `--wayback` and `--write-head`. `protocolith_verify` with `anchors` true also fails
with `ANCHOR_MISMATCH` (ledger rewritten), `ANCHOR_AHEAD` (truncated) or `ANCHOR_INVALID`.

## Prompts

| Name | Arguments | Content |
| --- | --- | --- |
| `research-agent-protocol` | none | Instructions for an AI agent: freeze before any run; record every run including failures and blocked sources; call `protocolith_claim_check` before stating any result and use its `may_say` wording; verify and anchor at the end and report the `anchor_id`. |

`prompts/list` returns `{"prompts": [{"name", "description", "arguments": []}]}`; `prompts/get` with `{"name": ...}` returns
`{"description", "messages": [{"role": "user", "content": {"type": "text", "text": ...}}]}`. An unknown name is `-32602`.

## Resources

Read-only, `mimeType` `application/json`.

| URI | Content |
| --- | --- |
| `protocolith://summary` | the same object as `protocolith_summary` |
| `protocolith://ledger` | `{"entries": [...], "head": {...}}` |
| `protocolith://schema/freeze` | JSON Schema of the protocol object |
| `protocolith://schema/record` | JSON Schema of a record body |
| `protocolith://schema/deviation` | JSON Schema of a deviation body |
| `protocolith://schema/issue` | JSON Schema of the `issue` input |
| `protocolith://schema/entry` | JSON Schema of a ledger line, with the stored body of each type in `$defs` |

An unknown URI is JSON-RPC error `-32002`. A ledger problem such as `NO_LEDGER` is `-32000` with the code at the start
of the message. The schemas are generated from the verifier's field rules; the verifier stays authoritative.

The normative text is section 5 of the [core specification](../spec/CORE_SPEC.md).
