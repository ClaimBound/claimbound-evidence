# Current Evidence Tracks

This page explains the current public ClaimBound tracks in plain language.

It is not a new result record. The source of truth remains the committed
protocols, sanitized artifacts, evidence cards and registry entries.

## Summary

| Track | Source | Public outcome | Interpretation |
| --- | --- | --- | --- |
| Grok prompts source audit | xAI Grok prompts GitHub repository | `PASSED_UNDER_PROTOCOL` | The public prompt repository passed the source-audit gate for repository availability, commit identity, README/LICENSE presence and prompt-file hashes only. |
| EEA source audit D-001 | EEA Air Quality Download Service | `PASSED_UNDER_PROTOCOL` | The public EEA download page passed the source-audit gate for page reachability, current download-service link and rights notice link only. |
| NASA POWER D-103 | NASA POWER Daily point API | `PASSED_UNDER_PROTOCOL` | A narrow renewable-resource signal passed the frozen gate for the documented points, period, target, controls and acceptance rule only. |
| NOAA CO-OPS D-131 | NOAA CO-OPS Data API | `NEGATIVE_RESULT_UNDER_PROTOCOL` | The official-source run completed, but the candidate did not pass the frozen acceptance gate. |
| NYC TLC Phase 4 | NYC TLC public trip records | Negative artifact | The official-source run completed, but the candidate did not pass all required controls. A full evidence card should be added or the record should remain clearly marked as artifact-only. |
| CDC mirror path | Public mirror path | Blocked-source style artifact | The proof path completed, but external source equivalence remained unresolved. No empirical pass or fail claim should be made. |

## Grok Prompts Source Audit

Grok prompts source audit is the current flagship "Where is the evidence?"
example for public AI transparency.

Allowed interpretation:

```text
The public xai-org/grok-prompts repository passed the source-audit gate for the
documented commit, repository metadata and prompt-file hash manifest.
```

Forbidden interpretation:

```text
This proves the live free Grok chat runtime uses exactly these prompts.
This proves there are no hidden server-side prompt or policy layers.
This proves Grok is safer, better or benchmark-superior.
```

The card is green only for the source-audit boundary. It is not a runtime model
equivalence result.

## EEA Source Audit D-001

EEA source audit D-001 is a green public-data source-boundary card.

Allowed interpretation:

```text
The EEA Air Quality Portal download page was reachable and exposed the expected
current download-service link and EEA copyright notice link.
```

Forbidden interpretation:

```text
This proves air-quality dataset coverage.
This proves pollutant, station or time completeness.
This makes a legal conclusion about data reuse.
```

This is separate from the larger EEA AQ D-001 manual PM10 track. That manual
track still needs a completed run or an honest blocked/insufficient outcome.

## NASA POWER D-103

NASA POWER D-103 is the current narrow positive example.

Allowed interpretation:

```text
NASA POWER D-103 passed the pre-registered gate under protocol 1.0.143 for the
documented points, period, target, candidate, controls and acceptance rule only.
```

Forbidden interpretation:

```text
This proves a universal forecasting edge.
This proves deployment readiness.
This proves superiority over all statistical methods.
This proves raw-byte reproduction.
```

The record was reproduced at outcome/gate level with source-byte drift. This
means the gate-level outcome was reproduced, but fresh source payload bytes
differed from the original payload bytes.

## NOAA CO-OPS D-131

NOAA CO-OPS D-131 is a negative official-source result.

Allowed interpretation:

```text
The official-source run completed, but the candidate did not pass the frozen
statistical acceptance gate.
```

This is useful evidence because it shows that the protocol can fail honestly.

Forbidden interpretation:

```text
The method passed under a different threshold.
The result can be renamed as success after the run.
The failed controls can be ignored.
```

## NYC TLC Phase 4

NYC TLC Phase 4 is a negative public artifact.

Allowed interpretation:

```text
The official-source run completed, but statistical acceptance did not pass under
the documented conditions.
```

Recommended cleanup:

- add a full evidence card; or
- keep the record clearly marked as artifact-only until a card exists.

## CDC Mirror Path

The CDC mirror path is a source-boundary example.

Allowed interpretation:

```text
The public mirror proof path completed, but source equivalence remained
unresolved.
```

This is a blocked-source style outcome. A technical pipeline can work while the
source boundary still prevents a performance claim.

## Why This Mix Is Good

A healthy ClaimBound repository should contain:

- positive records;
- negative records;
- blocked-source records;
- reproduction records;
- records with source-byte drift.

This makes the project more credible than a repository that publishes only
successful outcomes.
