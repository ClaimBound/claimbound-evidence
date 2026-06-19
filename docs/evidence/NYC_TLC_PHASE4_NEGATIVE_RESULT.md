# NYC TLC Phase 4 Negative Result

> **Artifact-only record.** This page and
> `artifacts/nyc_tlc_phase4_negative_result_summary.json` are **not** in the
> public registry. Do not cite them as validated evidence cards. See the
> [artifacts catalog](../artifacts/README.md).

Status: `NEGATIVE_RESULT_UNDER_PROTOCOL` (artifact narrative only)

## Summary

The NYC TLC Phase 4 real-source run used official-source 2023 yellow taxi hourly
pickup summaries for three borough scopes. The source audit passed, but the
statistical acceptance gate did not pass.

This is a negative result. It must not be presented as accepted evidence.

## Source Scope

```text
Source family: NYC TLC official-source yellow taxi trip records
Aggregation: hourly pickup summaries
Period: 2023
Scopes: MANHATTAN, BROOKLYN, QUEENS
Raw CSV/parquet committed: no
```

Input SHA-256 values:

| Scope | Rows | SHA-256 |
|---|---:|---|
| MANHATTAN | 8760 | `88d1f789fab56cfaeaed079302f5c59998f068768767b389ab906cb26193aa64` |
| BROOKLYN | 8760 | `f2a933fbf87921f6e9fdeac9f85b2c9299e6aeb4d64ac599288c606e3dcdedd4` |
| QUEENS | 8760 | `cefcaf54d9aa26fe6543bcab80846ce339f06cd7a792d3989103d23cf30457ac` |

## Outcome

```text
Source audit: passed
Windows: 45
Event-rate-in-range windows: 32
overall_go_no_go: false
result_status: NEGATIVE_RESULT_UNDER_PROTOCOL
```

Report SHA-256:

```text
c92b5fbd68c2391e0202b9c6840159679f32ed8c6c53288677f8e8d79bf253a8
```

## Failed Gates

The candidate did not pass every required control. In particular, the shuffled
control comparison did not meet the frozen positive-rate gate.

This was recorded as a failure, not as a near miss.

## Allowed Claim

```text
NYC TLC Phase 4 official-source proof-of-work completed; source audit passed
and statistical acceptance failed under the pre-registered protocol.
```

## Forbidden Claims

Do not claim:

- NYC evidence passed;
- universal forecasting edge;
- transport deployment readiness;
- public-health or energy claims from NYC evidence;
- near miss equals success.
