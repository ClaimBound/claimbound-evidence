# Independent Rerun Workflow

Independent reruns make ClaimBound cards stronger without turning the project
into a certification authority.

## When To Use This

Use this workflow when another operator wants to rerun an existing card and
publish an updated reproduction record or an honest non-pass.

Typical fields:

- `result_status`: the gate outcome under the frozen protocol
  (`PASSED_UNDER_PROTOCOL`, `NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE`
  or `INSUFFICIENT_COVERAGE`);
- `reproduction_level`: `REPRODUCED_OUTCOME` or
  `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` when another run confirms the
  outcome.

The rerun must stay inside the original claim boundary unless a new protocol is
opened.

## Request Path

1. Open a GitHub issue using the reproduction request template.
2. Link the original evidence card and protocol.
3. State expected rerun scope, source access risks and forbidden claims.

The issue is only a request. It is not reproduction evidence.

If you are new to the project, start with the
[external operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md). It explains
how to set up the repository, create a local run root and avoid publishing raw
payloads or overbroad claims.

For copy-paste commands and expected outputs, see
[examples/rerun/README.md](../examples/rerun/README.md).

## One-command reruns (any OS)

Frozen public-data reruns do not require bash, jq, curl or shasum on the primary
path. See [platform support](PLATFORM_SUPPORT.md).

```bash
uv run claimbound rerun nasa-d103 --operator "<your-handle>"
uv run claimbound rerun noaa-d131 --operator "<your-handle>"
uv run claimbound drift eea-source-audit
```

Or run VERIFY shortcuts:

```bash
uv run claimbound verify nasa-rerun --operator "<your-handle>"
uv run claimbound verify noaa-rerun --operator "<your-handle>"
uv run claimbound verify eea-drift
```

Tier packs: [external verification](external_verification/README.md).

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

Set `result_status` to the honest gate outcome from the rerun:

- `PASSED_UNDER_PROTOCOL` when the frozen gate passed;
- `NEGATIVE_RESULT_UNDER_PROTOCOL` when the gate did not pass;
- `BLOCKED_SOURCE` or `INSUFFICIENT_COVERAGE` when the source boundary blocks a
  fair result.

Set `reproduction_level` separately:

- `REPRODUCED_OUTCOME` when the original gate outcome is reproduced and source
  bytes remain stable;
- `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` when the gate-level outcome
  matches but fresh source bytes differ from the original raw payload bytes;
- `not independently reproduced` when no rerun has confirmed the outcome yet.

Do not put `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` in `result_status`.

## Verification

Before opening the PR:

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Do not edit thresholds, gates or claim boundaries to force a reproduced result.

## Source Drift And Boundary Questions

If a source changed but you are not ready to produce a rerun card, open a
`Source drift report` issue instead. If a card seems to imply more than the
evidence supports, open a `Card boundary question` issue. Neither issue type is
evidence by itself; both are triage paths for deciding whether a new rerun,
repair or documentation change is needed.
