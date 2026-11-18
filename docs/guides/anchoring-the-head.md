# Anchoring the head

## The gap

A valid ledger proves its own consistency. It cannot prove that it is *the* ledger. Anyone who can write the
file can build a new, valid ledger from scratch, or cut the last entries off an existing one, and verification
will pass. The head closes this gap if you record it somewhere you do not control alone.

## What the head is

```bash
protocolith head
# seq=2 hash=7e991c8d63f3f661894015c450b41cdb3809af305af4f562f8224466314eecd7
protocolith head --json
# {"count":3,"hash":"7e991c...","seq":2}
```

The hash of the last entry covers every earlier entry through the chain. One short value therefore stands for the
whole history up to `seq`.

`protocolith anchor` automates this: it writes a statement of the head, can time-stamp, archive or tag it, and
`verify-ledger --anchors` checks every anchor later. See [Anchor your results](anchor-your-results.md).

## Where to put it

| Anchor | What it gives you |
| --- | --- |
| A signed git tag or signed commit message in a repository others can read | Third-party-visible, signed by your key |
| A message in a channel others can read (issue, ticket, mailing list) | A visible time and place you cannot edit alone |
| A public timestamping service | An independent time for the value |
| A paper, a report or a preregistration page that quotes the head | Ties the claim to the history |
| A copy on another machine owned by someone else | Simple and effective |

None of these is built into Protocolith. Choose the one that fits who needs to trust you.

## Checking later

1. Run `protocolith head --json` on the ledger you are given.
2. Compare. If the ledger is longer than the anchor, the entry at the anchored `seq` must have the anchored
   hash (read it with `protocolith log --json`). If the ledger is shorter or has a different hash at that
   `seq`, the tail was removed or the history was replaced.

`protocolith verify-ledger --expect-head SEQ:HASH` does this for you:

```bash
protocolith verify-ledger --expect-head 2:7e991c8d63f3f661894015c450b41cdb3809af305af4f562f8224466314eecd7
# OK entries=3 head seq=2 hash=7e991c...
```

It first verifies the whole ledger. If that passes, it requires the entry at `SEQ` to exist and to have `HASH`;
otherwise it reports `HEAD_MISMATCH` and exits with 1 (for example when the tail was removed, or the history was
replaced). The value must be a decimal `SEQ`, a colon and 64 lowercase hex characters, else the command exits with 2.
A ledger that is longer than the anchor still passes: the check proves the anchored prefix is unchanged.

The option exists since 0.6.0. It cannot show that the anchor itself is trustworthy.

## When to anchor

At least once after freezing a protocol and before the run starts, and again after you record. A head anchored
before the run is the only thing that shows the protocol existed in that form before the result.

## Limits

An anchor shows the history existed in that form no later than the anchor's own time. The ledger's `ts` values
remain the appending machine's own claims.
