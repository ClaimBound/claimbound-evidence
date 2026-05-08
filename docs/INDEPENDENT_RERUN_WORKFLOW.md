# Independent Rerun Workflow

Independent reruns make ClaimBound cards stronger without turning the project
into a certification authority.

## When To Use This

Use this workflow when another operator wants to rerun an existing card and
publish one of these outcomes:

- `REPRODUCED_OUTCOME`;
- `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`;
- `NEGATIVE_RESULT_UNDER_PROTOCOL`;
- `BLOCKED_SOURCE`;
- `INSUFFICIENT_COVERAGE`.

The rerun must stay inside the original claim boundary unless a new protocol is
opened.

## Request Path

1. Open a GitHub issue using the reproduction request template.
2. Link the original evidence card and protocol.
3. State expected rerun scope, source access risks and forbidden claims.

The issue is only a request. It is not reproduction evidence.

## PR Path

1. Create a local run root outside this repository.
2. Read the original protocol before collecting fresh outcomes.
3. Record source access date, source URL, command and environment notes.
4. Keep raw payloads, transcripts and restricted source materials outside the
   repository.
5. Record raw hashes or a blocked-hashing reason.
6. Write a sanitized rerun summary under `artifacts/`.
7. Create a reproduction evidence card under `docs/evidence_cards/`.
8. Render SVG from the validated JSON card when applicable.
9. Update the registry only after validation.
10. Open a PR using the `I Reproduced This Card` template.

## Status Selection

Use `REPRODUCED_OUTCOME` only when the original outcome is reproduced under the
same protocol and the source boundary remains stable.

Use `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` when the gate-level outcome
matches but fresh source bytes differ from the original raw payload bytes.

Use `NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE` or
`INSUFFICIENT_COVERAGE` when that is what the rerun honestly finds.

## Verification

Before opening the PR:

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Do not edit thresholds, gates or claim boundaries to force a reproduced result.
