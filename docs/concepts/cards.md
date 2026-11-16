# Cards

`issue SEQ` renders a human-readable evidence card from a record. The card is derived data: it can be rebuilt
from the ledger at any time, and the ledger remembers its hash.

## What a card is built from

1. the record at `SEQ` (status, sources, reproduction level, claim boundary, reasons);
2. the frozen protocol it names (id, version, hash);
3. the optional `card` object inside the record body, which carries the remaining evidence-card fields
   (operator, source name and URL, domain, claim type, access date, hashes of the sanitized report, known
   limitations, and so on).

Fields derived from the record always win: a `card` key that contradicts them is rejected with `CARD_CONFLICT`.
Missing required fields are rejected with `MISSING_FIELD` and named; any other validation failure is
`CARD_INVALID`. The card is checked by the evidence-card validator before anything is written.

## Files

```text
.protocolith/cards/PLITH-<protocol_id>-<date of the record>.json
.protocolith/cards/PLITH-<protocol_id>-<date of the record>.svg
```

Change the folder with `--out DIR`. The JSON file is the canonical bytes of the card with no trailing newline,
so the SHA-256 of the file equals `card_sha256` in the `issue` entry. Issuing the same record again writes the
same bytes (and appends another `issue` entry). If the file exists with different content, the result is
`CARD_EXISTS` and nothing is overwritten. `raw_payload_committed` is always `false`.

## Rule R9

Verification rebuilds the card from the record and compares its hash with `card_sha256`. If the record, the
protocol or the evidence-card validator's output changed since, verification reports `BAD_CARD`.

## Reading a card

Read three fields first: `result_status`, `reproduction_level` and `claim_boundary`. A green card means one
narrow claim passed under one frozen protocol, not that a system is good. Most cards produced from a single
local run are `not independently reproduced`. The older card documentation is in the
[archive](../archive/README.md); the full list of fields is in [EVIDENCE_CARD](../EVIDENCE_CARD.md).
