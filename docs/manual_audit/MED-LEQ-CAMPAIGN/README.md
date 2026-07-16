# MED-LEQ manual source-boundary audit

- Frozen protocols: `MED-LEQ-01-D1201` through `MED-LEQ-12-D1212`.
- Separate reruns: the same IDs with `-R1`; baseline cards are not overwritten.
- Execution mode: `MANUAL_NO_AI`.
- Operator: `NeoZorK`.
- Access date: `2026-07-16`.
- Raw responses committed: `false`.

## D1208 overclaim review

| Public wording | Exact narrower source wording found | Population preserved? | Endpoint preserved? | Comparator preserved? | Time horizon preserved? | Honest status |
| --- | --- | --- | --- | --- | --- | --- |
| Leqembi cures Alzheimer's disease | reduction of decline / verified clinical benefit | No | No | No | No | `INSUFFICIENT_COVERAGE` |
| Leqembi reverses Alzheimer's disease | reduction of decline / verified clinical benefit | No | No | No | No | `INSUFFICIENT_COVERAGE` |
| Leqembi improves memory by 27% | reduction of decline / verified clinical benefit | No | No | No | No | `INSUFFICIENT_COVERAGE` |
| Twenty-seven percent of patients recovered | reduction of decline / verified clinical benefit | No | No | No | No | `INSUFFICIENT_COVERAGE` |

## Review decision

NEJM returned HTTP 403 and remains blocked. FDA qualifiers are preserved verbatim in meaning. The ClinicalTrials.gov boundary was fetched and hashed as part of the frozen source set but was not substituted into a card whose issue-defined primary boundary was NEJM or FDA.
