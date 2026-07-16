# Leqembi claim-boundary campaign

This public-interest audit covers issues #157–#161. It is not medical advice, an individual benefit prediction, or a benefit-risk recommendation.

## Claim-transformation map

```text
CDR-SB mean change at 18 months
  lecanemab 1.21 vs placebo 1.66; difference -0.45
                         |
                         v
relative arithmetic: 0.45 / 1.66 = 27.1%
                         |
                         v
headline shorthand: “slows decline by about 27%”
                         |
                         v
unsupported transformations in the selected FDA boundary
  “memory improves by 27%” | “27% recovered” | “reverses” | “cures”
```

The first four primary-paper cards remain `BLOCKED_SOURCE`: the frozen NEJM URL returned HTTP 403. No easier source was substituted. The arithmetic is preregistered, but it does not independently establish the inaccessible paper's clinical statements.

## Baseline results

| Protocols | Frozen source | Result |
| --- | --- | --- |
| `MED-LEQ-01-D1201`–`04-D1204` | NEJM primary-paper URL | `BLOCKED_SOURCE` (HTTP 403) |
| `MED-LEQ-05-D1205`–`07-D1207` | FDA 6 July 2023 announcement | `PASSED_UNDER_PROTOCOL` |
| `MED-LEQ-08-D1208` | FDA 6 July 2023 announcement | `INSUFFICIENT_COVERAGE` |
| `MED-LEQ-09-D1209`–`12-D1212` | FDA 6 July 2023 announcement | `PASSED_UNDER_PROTOCOL` |

The D1208 result records that the FDA page supports narrower language about reduction of decline and verified clinical benefit, not the four stronger public formulations. Mere absence was not relabelled as a negative result.

## Safety-language audit

The published boundaries preserve `infrequently`, ApoE ε4 homozygotes, comparison with placebo, association rather than causation, caution rather than prohibition, and possibility rather than certainty. A boxed warning is recorded without turning it into an overall benefit-risk conclusion.

## Immediate R1 drift table

| Baseline | Rerun | Baseline status | Rerun status | HTTP/access changed? | Claim support changed? | Byte drift? |
| --- | --- | --- | --- | --- | --- | --- |
| D1201–D1204 | D1201-R1–D1204-R1 | `BLOCKED_SOURCE` | `BLOCKED_SOURCE` | No | No | Yes (403 response body) |
| D1205–D1207 | D1205-R1–D1207-R1 | `PASSED_UNDER_PROTOCOL` | `PASSED_UNDER_PROTOCOL` | No | No | No |
| D1208 | D1208-R1 | `INSUFFICIENT_COVERAGE` | `INSUFFICIENT_COVERAGE` | No | No | No |
| D1209–D1212 | D1209-R1–D1212-R1 | `PASSED_UNDER_PROTOCOL` | `PASSED_UNDER_PROTOCOL` | No | No | No |

Exact baseline and rerun SHA-256 values, canonical URLs, HTTP results, matches, and protocol mappings are retained in the sanitized reports under `artifacts/leqembi_issue_*`. Raw responses remain only under the operator's local run root.

## Reproduce

```bash
uv run python scripts/claimbound_run_leqembi_campaign.py publish --operator <handle>
uv run claimbound validate-all
uv run --extra dev pytest -q
git diff --check
```

The publisher refuses duplicate protocol registration. Run it from a clean registry when creating a fresh campaign publication.
