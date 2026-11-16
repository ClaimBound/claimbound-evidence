# Result statuses

A record carries one `status` from a closed set. Anything else is rejected with `BAD_STATUS`. The set is the
one used by the evidence-card format, so issued cards stay valid under the card validator.

| Status | Use it when | Extra requirement in the core |
| --- | --- | --- |
| `PASSED_UNDER_PROTOCOL` | The run completed and met the frozen gate. | non-empty `sources` |
| `NEGATIVE_RESULT_UNDER_PROTOCOL` | The run completed and did not meet the gate. | non-empty `sources` |
| `BLOCKED_SOURCE` | Access, rights or lineage of the source did not allow a fair result. | `block_reason` |
| `INSUFFICIENT_COVERAGE` | The source exists but is too sparse or uneven for the protocol. | none |
| `SOURCE_DRIFT` | The source changed from what the protocol described. | `drift_reason` |
| `REPRODUCED_OUTCOME` | The primary outcome recorded is the reproduction of an earlier run. | non-empty `sources` |

A missing requirement is rejected with `MISSING_FIELD`.

## Rules of thumb

- **A negative result is a result.** Record it. Do not drop a failed run, and do not re-run until it passes
  without recording each attempt.
- **Absence of evidence is not a negative result.** If you could not get the data, use `BLOCKED_SOURCE` or
  `INSUFFICIENT_COVERAGE`.
- **Do not replace a blocked source after seeing a result.** If the protocol allows an alternative, say so before
  freezing; otherwise freeze a new version and say why.
- **A pass is narrow.** `PASSED_UNDER_PROTOCOL` means this gate on this source; the `claim_boundary` field says
  where the claim stops.

## Reproduction level

`reproduction_level` is a separate non-empty text field in the record. The core does not restrict it, but
`issue` needs one of the card values:

| Value | Meaning |
| --- | --- |
| `not independently reproduced` | Default for a first run. |
| `REPRODUCED_OUTCOME` | A rerun reached the same outcome. |
| `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | A rerun reached the same gate outcome but the source bytes differ. |

The status of a rerun that matches the gate outcome stays the gate outcome; the reproduction level is what
changes. The older description of these terms is in the [result status protocol](../RESULT_STATUS.md).
