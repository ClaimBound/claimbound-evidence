# Anchor your results

## The threat

A Protocolith ledger is a hash chain that its owner writes. It proves internal consistency, not authorship or time:
whoever can write the file can change an entry, recompute every later hash, and `protocolith verify-ledger` still passes.
The same holds for cutting off the last entries. If you are the only keeper of the ledger, a reader has to take your word that
it was not rewritten after you saw the result.

An **anchor** fixes the head of the ledger (its last `seq` and `hash`, which cover every earlier entry) in a place you
cannot edit alone. Later, `protocolith verify-ledger --anchors` compares every anchor with the ledger and reports

- `ANCHOR_MISMATCH`: the entry at an anchored position is not the anchored one, so the ledger was rewritten;
- `ANCHOR_AHEAD`: the ledger is shorter than an anchor says, so entries were removed;
- `ANCHOR_INVALID`: an anchor file or a stored time-stamp response was edited, damaged or deleted.

## What an anchor is

`protocolith anchor` writes an **anchor statement**: canonical JSON naming the head, the number of entries, the Protocolith
version and the time. Its sha256 is the `anchor_id`. Files go to `.protocolith/anchors/`:

```bash
protocolith anchor
# anchored seq=41 hash=3f9c... anchor_id=a1b2...
# .protocolith/anchors/41-3f9c0e1d22ab.json
# note: this anchor is local only; publish the statement or add --tsa, --wayback or --git-tag
```

A local anchor alone protects against accidents and against someone who edits the ledger but not the anchors folder. It does
**not** protect against someone who controls the whole store, because they can rewrite the anchors too. The protection comes
from a copy of the statement (or its hash) that lives somewhere else. Pick one or more of the options below.

## Five options

| Option | Time to evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| **Git tag** (`--git-tag`, then push) | a minute | the statement existed in your repository when you pushed it; a signed tag (`--sign`) also shows your key made it | the host's clock is not independent; you can delete and recreate a tag unless the repository is protected |
| **Release asset or Zenodo upload** (`--write-head FILE`, then attach or upload) | minutes | a third party now holds the exact statement bytes under a date and, on Zenodo, a DOI and checksum | the date is the platform's, not a cryptographic proof |
| **Software Heritage** (archive the repository that holds the statement) | minutes to hours | an independent archive holds the repository at that commit and gives it an identifier | it archives what you pushed; it does not know what the statement means |
| **Wayback Machine** (`--wayback URL`) | seconds | a public snapshot of the URL where you published the statement file | only useful if that URL served exactly the statement; the snapshot is not signed |
| **RFC 3161 time-stamp** (`--tsa URL`) | seconds | a time-stamp authority signed the statement hash at time T; this is the strongest standalone timestamp | Protocolith does **not** verify the signature; you verify it with `openssl` |

None of these is a secret keeper or a notary of your analysis. Choose by who must trust you: a regulator or reviewer will
usually accept a public time-stamp or an archive snapshot more readily than your own repository.

## Honest limits

- A timestamp proves that a record **existed** at time T. It does not prove that the analysis was **planned** earlier. To show
  that, freeze the protocol and anchor **before** you look at data, and keep the anchor of that earlier head.
  `claim_check` reports `protocol_frozen_before_record` only from the ledger's own timestamps, so a prospective claim needs an
  anchor taken after the freeze and before the record.
- An anchor shows the head did not change **after** the anchor. Entries before it are as trustworthy as the process that wrote
  them; the ledger does not check that a result is true.
- Entries appended after the last anchor are not covered yet. Anchor often, for example at the end of every session.
- Anchors from different methods are independent evidence. Several cheap ones beat one expensive one.

## Commands, end to end

```bash
# 1. work as usual
protocolith freeze protocol.json
protocolith record outcome.json

# 2. verify, then anchor locally and write the statement as a file you will publish
protocolith verify-ledger
protocolith anchor --write-head anchor-head.txt

# 3a. git tag (local; push it yourself)
protocolith anchor --git-tag --sign
git push origin anchor/41-3f9c0e1d22ab

# 3b. RFC 3161 time-stamp (a network request to the authority you name)
protocolith anchor --tsa https://timestamp.example/tsr
openssl ts -verify -in .protocolith/anchors/<anchor_id>.tsr \
    -data .protocolith/anchors/41-3f9c0e1d22ab.statement -CAfile ca.pem -untrusted tsa-cert.pem

# 3c. Wayback: publish anchor-head.txt at a public URL first, then ask for a snapshot of that URL
protocolith anchor --wayback https://example.org/study/anchor-head.txt

# 4. months later, or on another machine with the anchors folder and the ledger
protocolith verify-ledger --anchors
```

Each `anchor` run is idempotent for a head: the statement and `anchor_id` never change; only the list of methods grows.
`openssl ts -verify` needs the certificate bundle of the authority you used (`ca.pem`) and, if it is not inside the
response, the signer certificate (`tsa-cert.pem`); the output of `protocolith anchor --tsa` prints this command with your
file names. If a time-stamp or archive step fails, the local anchor and any method that succeeded earlier are kept.

To check against a published copy without the anchors folder, use the head: `protocolith verify-ledger --expect-head SEQ:HASH`
([anchoring the head](anchoring-the-head.md)), or compare the sha256 of the published statement file with the `anchor_id`.

## For AI agents

An agent should end a session with `protocolith_verify`, then `protocolith_anchor`, and report the `anchor_id` and the head with
its results. The MCP tool writes the local anchor and, with `tsa`, asks the named authority for a time-stamp; it cannot create
git tags or write files elsewhere. Before reporting a result, the agent calls `protocolith_claim_check`; the result says
whether the record is `anchored` and which claims it must not make. See [Use Protocolith from an AI agent](ai-agent-mcp.md).
