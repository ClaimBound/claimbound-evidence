# MCP integration

`protocolith mcp` runs a Model Context Protocol server on stdio, so an MCP client (an agent or an editor) can
freeze, record, verify, issue and query without a shell. It uses newline-delimited JSON-RPC 2.0, needs no third-party package, and writes only inside the store (the atlas and disclose tools
write one file each inside the working directory). It uses the network only when `protocolith_anchor` is called with a `tsa` URL.

This page is the short version. The step-by-step guide with a session transcript is
[Use Protocolith from an AI agent](ai-agent-mcp.md); the tools and resources are listed in the
[MCP reference](../reference/mcp.md).

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

## What the server offers

Fifteen tools (`protocolith_summary`, `protocolith_log`, `protocolith_show`, `protocolith_schema`,
`protocolith_capture`, `protocolith_atlas`, `protocolith_freeze`, `protocolith_record`, `protocolith_deviation`, `protocolith_verify`,
`protocolith_claim_check`, `protocolith_anchor`, `protocolith_disclose`, `protocolith_verify_disclosure`, `protocolith_issue`), read-only resources (`protocolith://summary`,
`protocolith://ledger`, `protocolith://schema/<name>`) and the prompt `research-agent-protocol`. Arguments not listed in a tool's schema are rejected. `isError` is true when an
operation was rejected or the ledger does not verify; the JSON then carries `codes`, `error` (with a `hint` where
there is one) and `violations`, exactly as with `--json`.

## Notes for agent use

- The server enforces the same rules as the CLI. An agent cannot write an entry that breaks a rule, but it can
  write any valid entry: decide who is allowed to freeze, and review what was frozen.
- `protocolith_issue` writes cards inside the store (`<store>/cards`); there is no output directory argument.
- `protocolith_capture` only reads files inside the server's working directory.
- A tool result is data. The ledger contents come from whoever wrote them; treat protocol text as untrusted
  input in your client.
