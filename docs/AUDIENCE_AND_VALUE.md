# Audience And Value

ClaimBound is useful when a public AI, ML or data-analysis claim should be
checked under rules fixed before the result is known.

The project is intentionally narrow. It is not a general model leaderboard,
paper index, experiment database, archive service or certification authority.

## Main Audiences

| Audience | Why ClaimBound helps |
| --- | --- |
| AI and LLM evaluation teams | Converts model, RAG, agent and benchmark claims into timestamped, source-bound evidence records. |
| Open-science researchers | Makes negative, blocked and reproduced outcomes publishable. |
| Funding reviewers and program evaluators | Provides a compact trail from protocol to source to status to limitation. |
| Data stewards and public-data teams | Makes source boundary, rights notes and coverage limits visible. |
| Civic-tech, journalism and watchdog projects | Supports transparent public-data checks without deployment claims. |
| ML researchers | Separates narrow evidence from broad model-superiority claims. |
| Educators | Teaches protocol discipline, baselines, controls and honest failure reporting. |
| Companies with AI products | Supports narrow customer-facing evidence cards instead of broad trust claims. |
| Independent verifiers, procurement teams and public buyers | Gives a clear path to request, rerun or challenge a result before adoption. |
| Public AI transparency readers | Connects familiar AI documentation claims to narrow source-audit cards. |

Detailed manual and AI-assisted workflow examples for the audience categories are in
[audience demonstration workflows](AUDIENCE_TESTIMONIAL_WORKFLOWS.md). The path
from those scenarios to real cards is defined in
[demo tracks to evidence cards](DEMO_TRACKS_TO_EVIDENCE_CARDS.md).

## Problem ClaimBound Solves

Many public AI/ML claims are hard to inspect because:

- the source boundary is unclear;
- the scoring rule is missing;
- the acceptance gate may have changed after seeing outcomes;
- payload handling is undocumented;
- negative results are not published;
- limitations are hidden or vague;
- reproduction level is not explicit.

ClaimBound makes these points visible in a compact evidence card.

## Worked Public Workflow

The public habit ClaimBound wants to support is simple:

```text
Where is the evidence?
```

For example, a public AI documentation claim can be turned into a narrow source
audit with URL, access date, expected markers, hash, result status, limitations
and rerun path. See the
[Grok prompt source-audit workflow](FLAGSHIP_WORKFLOW_GROK_EVIDENCE.md) for a
concrete worked example.

## What ClaimBound Adds

ClaimBound adds a thin evidence layer:

```text
frozen protocol
+ official public source
+ local payload policy
+ deterministic or auditable run path
+ exact result status
+ claim boundary
+ reproduction level
+ public card
```

## Why Negative Results Matter

A negative result under a fair protocol is useful. It says:

- the source was usable;
- the method was tested;
- the candidate did not pass the frozen gate;
- the failure should not be hidden or renamed as success.

This helps future operators avoid repeated weak claims.

## Why Blocked Results Matter

A blocked result is useful when the source cannot support a claim.

Examples:

- source access failed;
- source rights were unclear;
- coverage was insufficient;
- source lineage could not be verified;
- official-source equivalence was unresolved.

A blocked result prevents a technical proof path from becoming an unsupported
performance claim.

## Best-Fit Domains

Good early domains have official public sources, stable timestamps, clear units
and public value even when the result is negative.

Examples:

- air quality;
- weather and climate-derived records;
- renewable-resource time series;
- coastal and water-level records;
- public mobility and operations data;
- public infrastructure records;
- LLM forecast-resolution records;
- reproducible AI evaluation appendices.

## What ClaimBound Should Avoid

ClaimBound should avoid:

- private-source claims that cannot be sanitized;
- informal predictions without a resolution rule;
- broad model-superiority claims;
- deployment-readiness claims;
- payload redistribution when rights are unclear;
- subjective manual judgment after seeing outcomes;
- replacing source audit with model confidence.
