# Result Status Protocol v0.1

Every public evidence record must use one exact result status. The status is
the result. Card colors are only a visual aid.

## Statuses

| Status | Visual color | Required interpretation |
| --- | --- | --- |
| `PASSED_UNDER_PROTOCOL` | Green | The narrow claim passed only under the written protocol, source boundary and frozen gate. |
| `NEGATIVE_RESULT_UNDER_PROTOCOL` | Red | The source audit or run completed, but the candidate did not pass the frozen acceptance gate. No positive result claim is allowed. |
| `BLOCKED_SOURCE` | Amber | Access, rights, coverage, metadata, source lineage, model identity or scoring evidence was not good enough for a fair pass/fail result. |
| `INSUFFICIENT_COVERAGE` | Amber | The source exists, but usable coverage is too sparse or uneven for the pre-registered test. |
| `REPRODUCED_OUTCOME` | Green | A rerun reproduced the result status or gate-level outcome. |
| `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | Yellow | A rerun reproduced the result status or gate-level outcome, but fresh source payload bytes differed from the original payload bytes. Do not claim raw-byte reproduction. |

## Validity Colors

`card_validity_level` is separate from `result_status`.

| Validity color | Meaning |
| --- | --- |
| `GREEN_VALIDATED` | Required fields, status, claim boundary, hashes and public links validate. |
| `YELLOW_LIMITED_REPRODUCIBILITY` | The card is useful but has an explicit rerun or source-byte limitation. |
| `RED_INVALID_OR_TAMPER_EVIDENCE` | The card should not be treated as valid public evidence. |
| `GRAY_DRAFT_NOT_EXECUTED` | Request, scaffold or draft only. It is not evidence. |

Blocked cards can still be valid green cards when they honestly explain why no
empirical result should be claimed. Negative cards can still be valid public
evidence when they ran under the frozen protocol.

## Practical Reading Rule

Read every card in this order:

1. `result_status`: what happened under the protocol.
2. `claim_boundary`: what the card is allowed to prove.
3. `known_limitations`: what must not be claimed.
4. `reproduction_level`: whether another run confirmed the outcome.
5. `card_validity_level`: whether the card itself is complete enough to use.
