# ClaimBound Use Cases

ClaimBound is useful when a claim should be tested under rules fixed before the
run, and the result should remain useful even when it is negative, blocked or
only partially reproduced.

The framework is strongest when the source is public, the decision rule is
small enough to audit, and the claim boundary can be written in plain language.

## Primary Uses

| Use case | Question ClaimBound can answer | Public value |
| --- | --- | --- |
| Public-source forecast audit | Did a fixed signal pass a frozen gate on an official public source? | Reduces after-result tuning and selective reporting. |
| Environmental data method check | Did a pollution, weather or climate-resource signal survive baseline and control comparisons? | Creates reusable evidence for public-interest domains. |
| Energy-resource signal check | Did a renewable-resource shortfall signal pass a narrow protocol? | Separates narrow evidence from deployment claims. |
| Negative-result publication | Did a method fail under a fair protocol? | Prevents repeated work and makes failure informative. |
| Source-boundary audit | Was a source usable under rights, lineage and coverage rules? | Shows why a study was blocked before any performance claim. |
| Independent reproduction | Can another operator reproduce the same status or gate outcome? | Makes source drift and reproduction level explicit. |
| LLM forecast resolution | Did a timestamped model forecast resolve correctly against official sources? | Gives model claims a checkable trail instead of a screenshot. |
| Agent or tool claim check | Did a coding, research or analysis agent pass a frozen task gate? | Helps compare systems without changing the task after seeing output. |
| Research-method appendix | Can a paper or report link to a compact evidence record? | Adds a durable, reviewable companion to ordinary publication. |
| Teaching reproducible ML | Can students run, fail, reproduce and explain a protocol? | Trains audit discipline, not only leaderboard optimization. |
| Public infrastructure audit | Did a public operations signal pass a fixed protocol on official data? | Supports transparent civic analytics without deployment claims. |
| Climate-source audit | Is an official climate or weather-derived source usable under a protocol? | Makes source drift, coverage and rights visible. |
| AI evaluation report check | Does an AI evaluation claim have objectives, methods and uncertainty stated before reporting? | Encourages transparent evaluation practice. |
| Scientific reproducibility appendix | Can a result record preserve what was fixed, what changed and what reproduced? | Helps reviewers inspect a narrow evidence trail. |
| Cross-operator rerun | Did another operator reach the same status or find source-byte drift? | Turns reproduction into a first-class result. |
| Public data rights check | Can the source be used without raw payload redistribution? | Prevents evidence records from becoming data-rights problems. |

## Worked Workflow

The central public workflow is:

```text
public claim
  -> evidence request
  -> protocol scaffold
  -> manual or AI-assisted track
  -> hashes and deterministic report
  -> validated evidence card
  -> optional independent rerun
```

The worked Grok example shows how a public AI documentation claim becomes a
source-audit card instead of a broad model-ranking statement:
[Grok prompt source-audit workflow](FLAGSHIP_WORKFLOW_GROK_EVIDENCE.md).

Detailed scenario workflows for the audience categories are in
[audience demonstration workflows](AUDIENCE_TESTIMONIAL_WORKFLOWS.md). The
publication rule for completed demo cards is in
[demo tracks to evidence cards](DEMO_TRACKS_TO_EVIDENCE_CARDS.md).

## Evidence Card Pattern

Each public result should be reducible to a compact evidence card. The full
specification is in [docs/EVIDENCE_CARD.md](EVIDENCE_CARD.md).

```text
protocol_id:
status:
claim_boundary:
official_source:
access_date:
raw_payload_committed: false
raw_payload_hashes_or_manifest:
report_hash:
git_commit:
reproduction_level:
evidence_url:
```

The card should be shareable, but it should not be marketed as certification
unless there is an external review process with defined authority.

## LLM Forecast Track

A useful LLM track should test timestamped forecast claims, not general model
quality and not informal predictions.

Recommended fields:

```text
question:
forecast_deadline:
resolution_deadline:
model_or_system:
prompt_hash:
answer_timestamp:
probability:
allowed_sources:
resolution_rule:
scoring_rule:
result_status:
```

Good first scope:

- 10 to 30 questions;
- one narrow domain;
- official resolution sources only;
- Brier score or another pre-selected scoring rule;
- no prompt changes after the answer is recorded;
- ambiguous resolutions recorded as blocked, not forced into pass or fail.

## Where ClaimBound Should Not Be Used

ClaimBound is not the right public foreground for:

- informal or speculative claims;
- production alerts;
- legal certification;
- broad claims that a model is best overall;
- raw payload redistribution;
- private-source claims that cannot be sanitized;
- claims that need hidden subjective judgment after seeing the result.
- blockchain, token, wallet or on-chain storage features.
