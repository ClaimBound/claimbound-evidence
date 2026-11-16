# Local experiment workflow

A complete pass through one experiment, including the awkward cases. It assumes the
[quickstart](../getting-started/first-record.md) works for you.

## 1. Before the run

Write the protocol and freeze it.

```bash
protocolith freeze protocol.json
```

Check the entry with `protocolith log`. If you later realise the protocol was wrong, do not edit the file and
freeze again under the same version: that is rejected. Freeze a new version.

## 2. Run, outside Protocolith

Run your script. Keep what it produced where your normal data handling puts it. Protocolith stores hashes of
sources, not their content.

## 3. Hash the inputs

```bash
protocolith hash results.txt
```

The output is `<sha256>  <path>`. Use the 64-character hash in `sources`:

```json
"sources": [{"id": "results.txt", "sha256": "60ff5e00..."}]
```

## 4. A deviation, if there was one

If the run did not follow the protocol (a source moved, a step was skipped), record it first:

```json
{"protocol_sha256": "802a1675...", "kind": "source_change", "description": "The source file was re-exported."}
```

```bash
protocolith deviation deviation.json
# deviation source_change seq=3 hash=...
```

Then list its `seq` in the record: `"deviations": [3]`. A deviation must belong to the same protocol as the
record that lists it, otherwise verification reports `DANGLING_REF`. Listing a deviation is how a reader sees it
next to the result; a deviation that is never listed is still in the ledger.

## 5. Record

```bash
protocolith record record.json
```

If the clock of the machine moved backwards since the last entry, the record is rejected with `TS_REGRESSION`
(exit 2). Fix the clock; do not edit the ledger.

## 6. Verify and issue

```bash
protocolith verify-ledger
protocolith issue SEQ
```

## 7. Share

What you share is your decision: the ledger file, the card, or only the head. A reader who has the ledger can
verify it with the same command. A reader who has only the card can see its `protocol_sha256` and
`ledger_record_seq` but cannot verify the history.

## Several runs of one protocol

Record each run with its own `run_id`. Record failed and blocked runs too. Nothing stops you from recording many
runs against one frozen protocol; nothing hides them either.
