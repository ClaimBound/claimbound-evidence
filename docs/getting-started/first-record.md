# Your first record

This page walks through the four stages with the files in
[`examples/quickstart/`](../../examples/quickstart/). The same steps are run by
`tests/test_readme_examples.py`.

## 1. Set up a working directory

```bash
mkdir demo && cd demo
cp ../examples/quickstart/protocol.json ../examples/quickstart/record.json ../examples/quickstart/results.txt .
```

`protocol.json` is the question and the gate, written before the run:

```json
{
  "protocol_id": "QUICKSTART_D001",
  "version": "1",
  "question": "Does the example run pass at least half of its four checks?",
  "gate": "pass rate at least 0.5",
  "source": "results.txt"
}
```

`protocol_id` and `version` are required and name the protocol. Every other key is yours. Numbers must be
integers or strings: floats are rejected (see [canonical JSON](../concepts/canonical-json.md)).

## 2. Freeze

```bash
protocolith freeze protocol.json
```

```text
frozen QUICKSTART_D001 1 seq=0 hash=5bbd5c8c... protocol_sha256=802a1675aef8623a44d79272ca50c036ffc7c2d2ecd267ca440afdb19948369f
```

This creates `.protocolith/ledger.jsonl` with one line. `protocol_sha256` is the SHA-256 of the canonical bytes
of the protocol; it does not depend on whitespace or key order in your file. The entry `hash` depends on the time.

## 3. Record

`record.json` already names that `protocol_sha256` and the SHA-256 of `results.txt` (checked by the test suite).
In your own work you copy the hash that `freeze` printed, or compute it with `protocolith hash results.txt`.

```bash
protocolith record record.json
```

```text
recorded run-1 PASSED_UNDER_PROTOCOL seq=1 hash=e6fdb7f2...
```

A record is rejected, and nothing is written, if its protocol was not frozen earlier, if the status is not one of
the [result statuses](../concepts/result-statuses.md), or if a required field is missing.

## 4. Verify and issue

```bash
protocolith verify-ledger
protocolith issue 1
protocolith verify-ledger
```

```text
OK entries=2 head seq=1 hash=...
issued record seq=1 card_sha256=...
.protocolith/cards/PLITH-QUICKSTART_D001-<date>-000001.json
.protocolith/cards/PLITH-QUICKSTART_D001-<date>-000001.svg
OK entries=3 head seq=2 hash=...
```

`issue` builds the [card](../concepts/cards.md) from the record, the frozen protocol and the optional `card`
object of the record, validates it, writes JSON and SVG, and appends an `issue` entry. Open the SVG in a browser.

## 5. Look at the history

```bash
protocolith log
protocolith head
```

`head` prints the last `seq` and `hash`. That pair is what you can publish to make later removal detectable; see
[anchoring the head](../guides/anchoring-the-head.md).

## Break it on purpose

Change one character in `.protocolith/ledger.jsonl` (for example `PASSED` to `FAILED`) and verify:

```text
BAD_HASH line 1: hash does not match the recomputed value
BAD_CARD line 2: card_sha256 does not match the card rebuilt from the record
FAILED: BAD_CARD, BAD_HASH
```

The command exits with 1. "line N" is the zero-based index of the ledger line. The exact messages depend on
what you changed.

## Next

- [Local experiments](local-experiments.md): use the ledger around your own scripts.
- [Using it in CI](ci.md): exit codes and JSON output.
- [Concepts](../concepts/ledger.md): what the rules check.
