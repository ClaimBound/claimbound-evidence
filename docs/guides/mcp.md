# MCP integration

`protocolith mcp` runs a Model Context Protocol server on stdio, so an MCP client (an agent or an editor) can
freeze, record, verify and issue without a shell. It uses newline-delimited JSON-RPC 2.0, needs no network and no
third-party package, and writes only inside the store.

## Configure a client

```json
{
  "mcpServers": {
    "protocolith": {
      "command": "protocolith",
      "args": ["mcp", "--store", "/path/to/project/.protocolith"]
    }
  }
}
```

Use an absolute store path: a client may start the server in a different working directory. If `protocolith`
is not on the client's `PATH`, give the full path to the executable in your environment, or use
`uv --directory /path/to/checkout run protocolith mcp ...`.

## Supported methods

`initialize`, `ping`, `tools/list` and `tools/call`. The server answers with the protocol version the client
asks for if it knows it (`2025-06-18`, `2025-03-26`, `2024-11-05`), otherwise the newest. Notifications get no
answer. Unknown methods return JSON-RPC error `-32601`; malformed input `-32700` or `-32600`.

## Tools

| Tool | Arguments | Same as |
| --- | --- | --- |
| `protocolith_freeze` | `protocol` (object), optional `supersedes` | `protocolith freeze` |
| `protocolith_record` | `body` (object) | `protocolith record` |
| `protocolith_deviation` | `body` (object) | `protocolith deviation` |
| `protocolith_verify` | none | `protocolith verify-ledger` |
| `protocolith_issue` | `seq` (integer, at least 0) | `protocolith issue` |
| `protocolith_log` | none | `protocolith log` and `head` |

Arguments not listed are rejected (`additionalProperties` is false). Results are one text content item holding
canonical JSON. `isError` is true when the operation was rejected or the ledger does not verify; the JSON then
carries `codes` and `violations` exactly as with `--json`.

## Notes for agent use

- The server enforces the same rules as the CLI. An agent cannot write an entry that breaks a rule, but it can
  write any valid entry: decide who is allowed to freeze, and review what was frozen.
- `protocolith_issue` writes cards inside the store (`<store>/cards`); there is no output directory argument.
- A tool result is data. The ledger contents come from whoever wrote them; treat protocol text as untrusted
  input in your client.
