# CDC Mirror Source Boundary

> **Artifact-only record.** This page and
> `artifacts/cdc_mirror_source_boundary_summary.json` are **not** in the public
> registry. Do not cite them as validated evidence cards. See the
> [artifacts catalog](../artifacts/README.md).

Status: `BLOCKED_SOURCE` (artifact narrative only)

## Summary

A public mirror proof path was completed for weekly aggregate CDC-like flu
signals. The pipeline produced a real public-data run, but the source path was a
mirror route rather than a direct official export. A positive external claim is
therefore blocked until a direct export or accepted equivalence record exists.

This is a source-boundary record, not a positive empirical result.

## Source Scope

```text
Source path: public mirror route
Regions: NATIONAL, REGION_4, REGION_9
Rows: 430 per region
Windows: 5 per region
Raw payload committed: no
```

Report SHA-256:

```text
a15681422c1126db62e58c45c4e3fd2393993be471bc8ade42aec54ddb4e8ed3
```

## Outcome

```text
overall_go_no_go: false
result_status: BLOCKED_SOURCE
source boundary: direct-export or equivalence record required
```

## Why This Matters

The record shows that source lineage can block a claim even when a public data
pipeline runs end to end. Source eligibility is not the same thing as statistical
acceptance.

## Allowed Claim

```text
CDC mirror proof path completed; a positive external claim remains blocked by
source-equivalence requirements.
```

## Forbidden Claims

Do not claim:

- direct official export equivalence was proven;
- public-health readiness;
- positive empirical pass;
- universal forecasting edge;
- deployment readiness.
