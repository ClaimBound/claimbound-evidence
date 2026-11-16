# Statuses and versions: worked examples

These commands were run against the quickstart files. Hashes and times in your run will differ.

## A new version of the protocol

Copy `protocol.json` to `protocol_v2.json`, set `"version": "2"` and change the gate. Freeze it with the hash of
version 1:

```text
$ protocolith freeze protocol_v2.json --supersedes 802a1675aef8623a44d79272ca50c036ffc7c2d2ecd267ca440afdb19948369f
frozen QUICKSTART_D001 2 seq=1 hash=36bee7cd... protocol_sha256=c4a8359e...
$ protocolith freeze protocol_v2.json
protocolith: DUPLICATE_FREEZE: QUICKSTART_D001 version 2 is already frozen
  DUPLICATE_FREEZE line 2: QUICKSTART_D001 version 2 is already frozen
```

The second command exits with 2 and writes nothing.

## A blocked source

A record with status `BLOCKED_SOURCE` must give a reason. Without one:

```text
$ protocolith record blocked.json
protocolith: MISSING_FIELD: status BLOCKED_SOURCE requires: block_reason
```

With `"block_reason": "The source file could not be read."` added (and `"sources": []`, which is allowed for this
status), it is accepted:

```text
recorded run-2 BLOCKED_SOURCE seq=2 hash=3efd1efb...
```

## A negative result still needs its sources

```text
$ protocolith record neg.json        # status NEGATIVE_RESULT_UNDER_PROTOCOL, "sources": []
protocolith: MISSING_FIELD: status NEGATIVE_RESULT_UNDER_PROTOCOL requires: sources
```

A negative result is a completed run against hashed inputs. If there were none, the honest status is
`BLOCKED_SOURCE` or `INSUFFICIENT_COVERAGE`.

## A status that does not exist

```text
$ protocolith record bogus.json      # "status": "BOGUS"
protocolith: BAD_STATUS: status is not in the closed set: 'BOGUS'
```

## Issuing a record without card fields

`issue` needs the evidence-card fields. A record without a `card` object fails and names what is missing:

```text
$ protocolith issue 2
protocolith: MISSING_FIELD: card is missing fields: access_date, ai_assistance, claim_type, ...
```

Nothing is written. Add a `card` object like the one in `examples/quickstart/record.json` to the record before
recording it; a record cannot be edited afterwards.

## A deviation, then a record that lists it

```bash
protocolith deviation deviation.json        # prints: deviation source_change seq=3 hash=...
```

Then record with `"deviations": [3]`. See the [workflow guide](../guides/local-experiment-workflow.md).
