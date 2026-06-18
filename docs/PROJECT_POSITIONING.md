# ClaimBound Positioning

ClaimBound is a public evidence framework for narrow, pre-registered claims on
public sources.

The project should remain small, auditable and claim-boundary driven. Its value
comes from disciplined evidence records, not from trying to become a general
experiment platform, paper index, model leaderboard, archive service or
certification authority.

## Unique Strength

ClaimBound treats a result as a public evidence record with four properties:

1. The protocol and acceptance gate are fixed before outcome inspection.
2. The source boundary is audited before a performance claim is made.
3. Positive, negative, blocked and insufficient-coverage outcomes are all valid.
4. The final claim is narrow enough for another operator to challenge or rerun.
5. Manual and AI-assisted operation follow the same evidence rules.

The strongest public message is:

```text
ClaimBound turns a narrow public-source ML claim into a reproducible evidence
card with protocol, source lineage, hashes, status, claim boundary and
reproduction level.
```

## What ClaimBound Should Not Duplicate

ClaimBound should not duplicate established projects.

For scope boundary vs adjacent arXiv work (EviBound), see
[Related Work And Independence](RELATED_WORK_AND_INDEPENDENCE.md).

| Existing project type | Already covered elsewhere | ClaimBound boundary |
| --- | --- | --- |
| Experiment database | Datasets, tasks, runs and many model setups | Store only compact evidence records for narrow public claims. |
| Preregistration platform | Full study-plan registration and review workflows | Keep protocol files close to runnable code and evidence artifacts. |
| DOI archive | Long-term archival deposit and citation infrastructure | Link to archives when useful; do not become an archive. |
| Paper or code index | Paper discovery, code links and leaderboard tables | Publish evidence cards, not paper rankings. |
| Large benchmark suite | Broad model capability and safety evaluation | Keep small protocols that can be audited and rerun. |
| Model leaderboard | General ranking across many systems | Avoid global ranking as the primary product. |
| Certification service | Legal or institutional approval | Provide evidence records only, unless an external review process exists. |

## Non-Negotiable Boundaries

The public repository should not contain:

- private-source claims;
- informal predictions without an official resolution rule;
- market, investment or price claims;
- broad model superiority claims;
- deployment-readiness claims;
- raw payloads without clear redistribution rights;
- hidden manual judgment after seeing outcomes;
- blockchain, token, wallet or on-chain storage features.

## Role Of ML

ML is a candidate method inside a protocol, not the product by itself.

ClaimBound should use ML for:

- fixed candidate signals;
- baseline and control comparisons;
- public-source time-series evaluation;
- source and coverage diagnostics;
- LLM forecast resolution when the question, timestamp, source and scoring rule
  are frozen before resolution.
- automated report validation when validation rules are deterministic.

ClaimBound should not use ML for:

- broad claims that a model is best overall;
- tuning thresholds after seeing the outcome;
- replacing source audit with model confidence;
- producing unsupported claims from private or ambiguous sources.
- approving a result without protocol and evidence-card validation.

## Forecasts

A forecast is acceptable only when it is a checkable claim:

```text
question + timestamp + fixed model or method + deadline + official resolution
source + scoring rule + result status
```

The purpose is not to publish open-ended predictions. The purpose is to test
whether a previously recorded claim resolves under a rule that was fixed before
the answer was known.

## Domains

Good domains have:

- public official sources;
- stable access terms;
- clear units and timestamps;
- enough coverage for a frozen gate;
- obvious baselines and negative controls;
- public value even when the result is negative.

Recommended early domains:

- environmental measurements;
- renewable-resource time series;
- public mobility or operations data when rights are clear;
- official climate or weather-derived records;
- public infrastructure and operations data with stable official sources;
- public scientific source-boundary audits;
- reproducible AI evaluation reports;
- narrow LLM forecast-resolution records.

Avoid domains where the public record would require private data, ambiguous
source rights or after-result interpretation.
