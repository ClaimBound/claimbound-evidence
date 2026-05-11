# NOAA_COOPS_D131 Pre-Registration Charter

Status: public protocol record for the committed negative result. Existing
card:
[CLAIMBOUND-NOAA-COOPS-D131-2026-04-30](../evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json).

Protocol version:

```text
1.0.139
```

## Claim Boundary

This protocol can check only the documented NOAA CO-OPS D-131 source, station,
period and statistical gate. It must not claim coastal-warning deployment
readiness, universal forecasting performance or superiority over all
statistical methods.

## Source Scope

```text
Official source: https://api.tidesandcurrents.noaa.gov/api/prod/datagetter
Observed product: hourly_height
Prediction product: predictions
Prediction interval: h
Datum: MLLW
Time zone: gmt
Units: metric
Format: json
Period: 2018-01-01..2024-12-31
Stations: 8518750, 9414290, 8638610
Raw payload committed: false
```

## Acceptance Gate

Record `PASSED_UNDER_PROTOCOL` only when:

- source audit passes;
- at least three eligible stations are available;
- at least the required eligible windows are available;
- the candidate passes all frozen baseline, residual and event-rate gates.

Record `NEGATIVE_RESULT_UNDER_PROTOCOL` when the official-source run completes
but any frozen acceptance gate fails.

## Recorded Negative Outcome

The committed D-131 card recorded:

```text
source_audit_passed: true
eligible_station_count: 3
eligible_windows: 11
overall_go_no_go: false
result_status: NEGATIVE_RESULT_UNDER_PROTOCOL
```

Failed gates:

- seasonal hour-of-year residual control was not beaten;
- event rate was below the minimum in one window;
- event rate was above the maximum in one window.

## Forbidden Claims

Do not claim:

- D-131 passed;
- coastal-warning performance was proven;
- universal forecasting edge;
- deployment readiness;
- all statistical methods were beaten.
