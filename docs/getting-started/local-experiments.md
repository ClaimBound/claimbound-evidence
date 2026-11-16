# Local experiments

Protocolith does not run anything. You run the experiment with your own scripts and use three small JSON files
around it. The loop is the same for every experiment.

## The loop

1. Write `protocol.json`: the question, the data you will use, the exact gate, how a failed run is reported.
   Keep it small; anything you want to be unable to change later belongs here.
2. `protocolith freeze protocol.json`. Do this before the first run. From now on the protocol is identified by
   its hash.
3. Run your experiment. Keep raw outputs outside the repository or ignored by git; Protocolith never stores raw
   payloads, only hashes.
4. Hash each input the run used (`protocolith hash FILE`, or `shasum -a 256`, or `Get-FileHash` on Windows)
   and write `record.json` with the outcome, the source hashes and a `claim_boundary` that says where the claim stops.
5. `protocolith record record.json`, then `protocolith verify-ledger`.
6. Optional: `protocolith issue SEQ` to produce a card.

## Where the store lives

By default `.protocolith/` in the current directory. Use `--store DIR` or the environment variable
`PROTOCOLITH_STORE` to keep one ledger per project or to keep the store outside the working tree:

```bash
export PROTOCOLITH_STORE="$HOME/experiments/ledgers/my-project"
```

Whether to commit `.protocolith/ledger.jsonl` to git is your decision. Committing it gives you history and a
way to compare against an earlier copy; it is not a replacement for anchoring the head
([guide](../guides/anchoring-the-head.md)). Add `.protocolith/lock` to `.gitignore`.

## If the run does not go to plan

- The source changed or is unavailable: record `BLOCKED_SOURCE` with a `block_reason`, or `SOURCE_DRIFT` with a
  `drift_reason`. Do not swap the source after seeing a result.
- Too little data for the gate: `INSUFFICIENT_COVERAGE`.
- You had to do something the protocol did not allow: record a `deviation` first, then list its `seq` in the
  record's `deviations`.
- The protocol itself was wrong: freeze a new version with `--supersedes`; the old record keeps pointing at the
  old hash.
- The gate was not met: record `NEGATIVE_RESULT_UNDER_PROTOCOL`. A failed run is a result, not an error.

Absence of evidence is not a negative result; use the blocked or coverage statuses for it. See
[result statuses](../concepts/result-statuses.md) and [the worked examples](../examples/statuses-and-versions.md).

## One ledger or many

A ledger can hold many protocols and many runs; verification checks each record against the protocol it names.
Separate ledgers make sense when you want to anchor, share or delete them independently.
