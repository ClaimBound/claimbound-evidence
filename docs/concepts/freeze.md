# Freeze

Freezing records a protocol in the ledger as a `freeze` entry. After that, every record and deviation that names
the protocol is checked against it.

```bash
protocolith freeze protocol.json
protocolith freeze protocol_v2.json --supersedes 802a1675aef8623a44d79272ca50c036ffc7c2d2ecd267ca440afdb19948369f
```

## What the entry holds

`protocol_id`, `version`, the whole `protocol`, `protocol_sha256` (the hash of `protocol`) and `supersedes`
(the hash of the version it replaces, or null).

## Rules that apply

| Situation | Result |
| --- | --- |
| The same `(protocol_id, version)` is frozen twice | rejected, `DUPLICATE_FREEZE` (R6) |
| `supersedes` names a hash that was not frozen earlier, or one of another `protocol_id` | rejected, `UNKNOWN_PROTOCOL` |
| `protocol_id` or `version` in the entry differs from the protocol object | rejected, `BAD_ENTRY` |

A rejected freeze exits with code 2 and writes nothing.

## A new version

```text
seq 0  freeze  DEMO_D001 version 1
seq 1  record  (names the hash of version 1)
seq 2  freeze  DEMO_D001 version 2, supersedes the hash of version 1
seq 3  record  (names the hash of version 2)
```

The record at seq 1 is still valid and still points at version 1. Supersession does not rewrite history; it adds
a visible step. A reader sees that the protocol changed after a result was recorded, which is the point.

## What freezing does not do

It does not prove when you froze. The timestamp is the machine's clock. It proves order: the freeze entry comes
before the records that name it, and the chain makes it impossible to insert a freeze earlier without breaking
the hashes of every later entry. See [what the ledger proves](ledger.md#what-the-ledger-proves-and-does-not).
