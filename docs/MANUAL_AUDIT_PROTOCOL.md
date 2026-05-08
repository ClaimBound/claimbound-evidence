# Manual Audit Protocol

Manual audit is a first-class ClaimBound path. It is not a fallback for missing
automation.

Manual tracks are useful when source rights, station selection, units, coverage
or resolution rules require careful operator judgment before a run.

## Manual Audit Rule

The operator must write down all judgment rules before outcome scoring.

```text
Manual judgment is allowed before scoring.
Manual judgment after scoring is a deviation.
```

## Required Manual Steps

1. Identify the official source.
2. Create a local run root:
   `uv run claimbound run-root --protocol-id <ID> --source-url <URL>`.
3. Read source rights and attribution requirements.
4. Decide raw payload handling.
5. Fix domain, period, target, candidate, baselines and controls.
6. Fix coverage rules.
7. Fix acceptance gate.
8. Write forbidden after-result changes.
9. Download or access source data into the local run root, not the repository.
10. Hash raw payloads when possible.
11. Run the parser, runner or manual scoring sheet.
12. Record deviations in `DEVIATIONS.md`.
13. Publish exact result status.

## Manual Operator Declaration

Each manual track should include:

```text
I fixed source, selection, target, candidate, baselines, controls, coverage
rules and acceptance gate before outcome scoring.

I did not remove weak data after seeing outcomes.
I did not tune thresholds after seeing outcomes.
I did not rewrite a negative or blocked outcome as a positive claim.
I recorded deviations and limitations.
```

## Manual Result Status

Manual audit must choose one documented status:

- `PASSED_UNDER_PROTOCOL`;
- `NEGATIVE_RESULT_UNDER_PROTOCOL`;
- `BLOCKED_SOURCE`;
- `INSUFFICIENT_COVERAGE`.

Any status is acceptable when honestly recorded.

## Manual Review Checklist

- [ ] Official source is identified.
- [ ] Local run root exists outside the repository.
- [ ] Source rights are recorded.
- [ ] Raw payload policy is recorded.
- [ ] Source access date is recorded.
- [ ] Protocol is fixed before scoring.
- [ ] Selection rule is fixed before scoring.
- [ ] Coverage rule is fixed before scoring.
- [ ] Baselines and controls are fixed before scoring.
- [ ] Acceptance gate is fixed before scoring.
- [ ] Raw hashes or block reason are recorded.
- [ ] Deviations are recorded in the deviation log.
- [ ] Result status is exact.
- [ ] Claim boundary is narrow.
- [ ] Evidence card is complete.

## When To Stop

Stop and record a blocked or insufficient-coverage outcome when:

- official source cannot be identified;
- source rights are unclear;
- timestamps, units or metadata are not usable;
- coverage is too weak for the frozen gate;
- raw payloads cannot be handled under repository policy;
- the operator cannot reconstruct the exact selection rule.
