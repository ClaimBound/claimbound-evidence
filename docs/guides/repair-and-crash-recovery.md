# Repair and crash recovery

## What a crash can do

An append is `write` + `flush` + `fsync` of one complete line under an exclusive lock. If the process or the
machine dies in the middle of a write, the file can end with a partial line (no final newline). Nothing else is
modified: earlier lines are never rewritten.

## What you will see

```text
$ protocolith verify-ledger
TRUNCATED_TAIL line 3: last line is not terminated by a newline
FAILED: TRUNCATED_TAIL
```

Exit code 1. Further appends are refused while the tail is partial (they report `VERIFICATION_FAILED`, exit 1),
because Protocolith never appends after a damaged line.

## Repair

```bash
protocolith repair --truncate-partial-tail
# removed 13 bytes of partial tail
protocolith verify-ledger
```

`repair` removes only the unterminated last line, and only if everything before it verifies. If the rest of the
ledger does not verify, it refuses and reports why; if there is no partial tail, it exits with 2 and
`NO_PARTIAL_TAIL`. It is the only command that shortens the file, and it requires the explicit flag.

The entry that was being written is lost; its effect did not happen as far as the ledger is concerned. Run the
command that failed again.

## What repair cannot fix

| Symptom | Meaning | What to do |
| --- | --- | --- |
| `BAD_HASH`, `BAD_PREV`, `BAD_SEQ` in the middle | The file was changed or damaged | Restore from a backup or from git; do not edit. |
| `NOT_CANONICAL` | A line was reformatted by an editor or a tool | Restore the original bytes. |
| Mixed line endings after a transfer | A tool converted `\n` to `\r\n` | Restore; keep the file as binary in git (`-text`). |
| `BAD_CARD` | The card cannot be rebuilt from the record | Restore; check that you did not change the record or the card validator version. |
| Lock timeout (`LOCK_TIMEOUT`, exit 3) | Another process holds the lock | Wait or stop that process. A stale lock file is harmless: the lock is released when the holder dies. |

Do not repair by editing the ledger or recomputing hashes. A repaired ledger that you re-hash yourself verifies,
but it is no longer the history you want to show.

## Backups

Copy the ledger file after important steps and compare the head against an anchored value
([anchoring](anchoring-the-head.md)). Keep `.gitattributes` rule `*.jsonl -text` if you store the ledger in git on
Windows.
