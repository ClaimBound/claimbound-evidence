# Query the ledger quickly

Four read commands answer most questions. They never write, and they work on a ledger of tens of thousands of
entries in well under a second (`summary` on 10,000 entries takes about as long as one `verify-ledger`).

## What was done, and are the results honest?

```bash
protocolith summary
```

```text
ledger OK  entries=3  head seq=2 hash=6c46d744...
entries: freeze 1, record 1, deviation 0, issue 1
results: PASSED_UNDER_PROTOCOL 1
PROTOCOL         VERSIONS  LATEST  RECORDS  LATEST_STATUS          DEVIATIONS  CARDS
QUICKSTART_D001  1         1       1        PASSED_UNDER_PROTOCOL  0           1
problems: none
```

The first line is the verification verdict and the head. Then come the counts by entry type and by result status, one row
per protocol (all its versions, the latest version, records, the status of the latest record, deviations and issued
cards) and the problems found. If the ledger does not verify, `summary` still prints what it could read, lists the
violations under `problems` and exits with 1. `--protocol ID` limits it to one protocol; `--json` prints canonical JSON.

## Filter the log

```bash
protocolith log --protocol QUICKSTART_D001 --type record
protocolith log --status BLOCKED_SOURCE          # only records with that status
protocolith log --tail 5                         # the last five entries
protocolith log --type issue --tail 1 --json
```

Filters combine. An unknown protocol is an error (`UNKNOWN_PROTOCOL`) rather than an empty list.

## Look at one entry

```bash
protocolith show 1
```

It prints the entry, the protocol it belongs to (and the `seq` where that protocol was frozen), the entries it points
at (for a record: its deviations; for an issue: its record) and the entries that point at it.

## Capture the environment and inputs

```bash
protocolith capture --file results.txt --env
```

```json
{"environment":{"machine":"arm64","platform":"darwin","protocolith":"0.6.0","python":"3.13.1"},"inputs":[{"path":"results.txt","sha256":"60ff5e00...","size":34}]}
```

Paste the fragment into the `outcome` object of your record. It runs nothing, reads no environment variable values,
and only hashes files inside the current directory (with relative paths).

## See the formats

```bash
protocolith schema record
```

prints the JSON Schema of a record body; `protocolith schema` prints all of them. They are generated from the same
rules the verifier uses.

## Start a store, and read errors

`protocolith init` creates an empty store and prints its path; repeating it changes nothing. Errors end with a one-line
hint saying what to do, for example `hint (NO_LEDGER): run protocolith freeze FILE ...`.

From Python: `core.summary(store)`, `core.log(store, type="record", tail=5)`, `core.show(store, 1)`. From an agent: the
tools and resources in the [MCP reference](../reference/mcp.md).
