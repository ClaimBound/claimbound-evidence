# Deviation Log And Source-Rights Checklist

Every local run root created by `claimbound run-root` contains two operator
records. Both stay local with the run root; do not commit raw payloads.

## Deviation log

`deviations.jsonl` is append-only, one JSON object per line, with these fields:

| Field | Meaning |
| --- | --- |
| `timestamp` | UTC time the entry was written |
| `step` | Protocol step affected |
| `planned` | What the frozen protocol planned |
| `happened` | What actually happened |
| `reason` | Why it differed |
| `who` | Operator who recorded it |

```bash
claimbound run-root deviation add --run-dir RUN_DIR --step fetch \
  --planned "fetch 30 points" --happened "fetched 28" \
  --reason "HTTP 404 on two points" --who operator-handle
claimbound run-root deviation list --run-dir RUN_DIR
```

`list` validates every line and fails on malformed entries. Entries are never
edited or removed by the tool; correct a mistake by adding a new entry. A
deviation does not change a result status by itself, and recording one is not
a way to reclassify an outcome. The human-readable `DEVIATIONS.md` template
remains for narrative notes.

## Source-rights checklist

`SOURCE_RIGHTS_CHECKLIST.md` lists operator questions about terms of use,
robots/access policy, attribution, redistribution, rate limits and personal
data. Record answers in the source's own words:

```bash
claimbound run-root rights answer --run-dir RUN_DIR --question-id robots \
  --answer "robots.txt has no Disallow for the fetched path" --who operator-handle
```

Answers are appended to `source_rights_answers.jsonl`. The checklist records
what the operator observed. It is not a legal conclusion and does not assert
that any use is permitted.
