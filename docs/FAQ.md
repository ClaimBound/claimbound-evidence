# FAQ

## What is Protocolith in one sentence?

A small local ledger that records a protocol before a run, records the outcome after, lets anyone verify that
the history is intact and every record follows its frozen protocol, and issues a card from a verified record.

## Why a new name?

The project was published as ClaimBound Evidence until 0.5.0. Two unrelated works use a very similar name, and
the project did not want to be mistaken for either. Old releases stay available under the old name and in git
history. The note on [related work and independence](RELATED_WORK_AND_INDEPENDENCE.md) lists those works and
what separates them from this one. The rename does not imply a new owner, a fork or an affiliation.

## What is it not?

- Not a tool that runs experiments, fetches data or schedules jobs.
- Not a judge of whether a protocol is scientifically good, or of whether a result is true.
- Not a certification authority, a hosted service or a leaderboard.
- Not a clock: it does not prove when something happened.
- Not tamper-proof by itself: see "Can someone rewrite the ledger?" below.

## How is it different from experiment trackers and workflow tools?

Those tools help you run and organise work: they log parameters and metrics, launch jobs, manage pipelines.
Protocolith is narrower. It keeps one append-only record of what you committed to before the run and what you
reported after, with rules that reject a record that does not follow its frozen protocol. You can use it next to
a tracker or a pipeline: the tracker holds the run details, Protocolith holds the commitment and the verdict,
and a source hash links the two. It has no server, no database and no web interface.

## Can someone rewrite the ledger?

Anyone who can write the file can build a new valid ledger, or remove the last entries, and `verify-ledger`
will still pass. The ledger proves internal consistency and ordering, nothing else. To make rewriting visible,
anchor the head (see below).

## How do I anchor the head?

Run `protocolith head`, and publish the printed `seq` and `hash` somewhere you do not control alone: a signed git
tag, a message others can read, a timestamping service, a copy held by someone else. Later, compare the head
of the ledger you are given with the anchored one. The full procedure is in
[anchoring the head](guides/anchoring-the-head.md). The check is
`protocolith verify-ledger --expect-head SEQ:HASH`.

## Do the timestamps prove when something was recorded?

No. `ts` is the clock of the machine that appended. Verification only checks that it never decreases. An
anchored head gives you a time no later than the anchor's own time.

## What should I do after a crash?

Run `protocolith verify-ledger`. If it reports only `TRUNCATED_TAIL`, a write was interrupted:
run `protocolith repair --truncate-partial-tail`, verify again and repeat the command that did not finish. For
any other code, do not edit the file; restore it from a backup. Details: [repair and crash recovery](guides/repair-and-crash-recovery.md).

## I made a mistake in a record. Can I fix it?

You cannot edit or delete entries. Record a `deviation` that describes the mistake, or record a new run, and
freeze a new protocol version if the protocol was wrong. The earlier entries stay, which is the point.

## Can I change a protocol after freezing?

No. Freeze a new version with `--supersedes`. Records made under the old version keep pointing at the old hash,
so a reader can see that the protocol changed and when.

## Why are floats not allowed?

Floats have several textual forms and different rounding in different languages, which would make hashes
differ. Write decimals as strings (`"0.001"`) or as integers in a fixed unit.

## Where are the raw data?

Not in Protocolith. It stores hashes of sources, never their content; `raw_payload_committed` on a card is
always `false`. Keep raw data where your data policy says.

## Does a green card mean the claim is true?

No. `PASSED_UNDER_PROTOCOL` means one narrow gate passed on one source, as recorded by whoever ran it. Read
`claim_boundary` and `reproduction_level`. A run by one operator stays `not independently reproduced` until
someone else records a rerun.

## Does it work offline? On Windows? In CI?

Yes to all three. There is no network access, the supported systems are macOS, Linux and Windows, and it runs
headless. See [install](getting-started/install.md) and [using it in CI](getting-started/ci.md).

## Is it used by anyone? Is it a standard?

This documentation makes no claim of adoption. The specification is a draft, version 0.1, with one
implementation. It is not a standard and makes no claim of priority.

## How do I report a security problem?

See [SECURITY.md](../SECURITY.md). Do not open a public issue.
