# Reading a card

An evidence card answers one question about one claim. These fields matter most:

| Field | Question it answers |
| --- | --- |
| `claim_boundary` | What exactly does this card show, and where does it stop? |
| `result_status` | What did the frozen gate say? |
| `reproduction_level` | Has anyone reproduced it? |
| `verification_level` | How many operators, and were they independent? |
| `official_source_url`, `access_date` | Which public source, and when was it read? |
| `sanitized_report_sha256` | Which report do the hashes refer to? |
| `execution_mode` | Manual or AI-assisted provenance. |
| `known_limitations` | What the maintainer already knows the card does not cover. |

## Result status

| Status | Meaning |
| --- | --- |
| `PASSED_UNDER_PROTOCOL` | The narrow claim passed the frozen gate. Not a statement about general quality or safety. |
| `NEGATIVE_RESULT_UNDER_PROTOCOL` | The check completed and the candidate did not pass. |
| `BLOCKED_SOURCE` | The source could not support a fair verdict (access, rights, lineage). |
| `INSUFFICIENT_COVERAGE` | The source is too sparse for the pre-registered test. |

Colors on the SVG are a visual aid; the exact strings are authoritative. See the full
[result status protocol](RESULT_STATUS.md).

## Reproduction

A rerun that reaches the same outcome with the same source bytes gives `REPRODUCED_OUTCOME`.
If the source bytes changed but the gate outcome is the same, the level is
`REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` (yellow chip). It is not a failed gate.

The [evidence card protocol](EVIDENCE_CARD.md) lists every field. The
[common misreadings](COMMON_MISREADINGS.md) page covers the mistakes readers make most often.
