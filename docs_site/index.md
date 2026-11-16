# Protocolith

**Records, verifies and issues trial records.**

Freeze a protocol before a run, record the outcome, verify the hash-chained history, issue a card. One local
append-only ledger, a command line (`protocolith`, alias `plith`), a Python API and an MCP server. Standard
library only; Python 3.11 to 3.15; macOS, Linux and Windows; headless.

```bash
protocolith freeze protocol.json
protocolith record record.json
protocolith verify-ledger
protocolith issue 1
```

## Start here

<div class="grid cards" markdown>

- **Try it in two minutes**

    [Install](getting-started-install.md) · [Your first record](getting-started-first-record.md)

- **Understand it**

    [Ledger and hash chain](concepts-ledger.md) · [Result statuses](concepts-result-statuses.md) · [Canonical JSON](concepts-canonical-json.md)

- **Use it**

    [Local experiments](getting-started-local-experiments.md) · [CI](getting-started-ci.md) · [Use it from an AI agent](guides-ai-agent-mcp.md) · [Query the ledger](guides-query-the-ledger.md) · [Python API](guides-python-api.md)

- **Look it up**

    [Command reference](CLI.md) · [MCP tools](reference-mcp.md) · [Core specification](spec-core.md) · [Error codes](reference-error-codes.md)

</div>

## What it proves, and what it does not

A valid ledger proves **internal consistency and ordering**. It does not prove wall-clock time, and it cannot
detect that a whole ledger was replaced or its tail removed unless you anchored the head somewhere else
([anchoring the head](guides-anchoring-the-head.md)). It does not show that a protocol is sound or that data is
true. Check against an anchored head with `verify-ledger --expect-head SEQ:HASH`.

## Status

The ledger commands are on the development branch toward 0.6.0 and installable from source today; the specification
is a draft (0.1) with one implementation. See the [roadmap](project-roadmap.md) and the [FAQ](FAQ.md).

The earlier evidence-card material (card validators, runners, registry views) is kept under
[Archive and examples](archive.md). The project was published as ClaimBound Evidence until 0.5.0; see
[related work and independence](RELATED_WORK_AND_INDEPENDENCE.md).
