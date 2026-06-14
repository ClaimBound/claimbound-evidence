# Lightweight Software R&D Claim Discipline

Status: methodology note. This page is not an evidence card, empirical result,
endorsement, production-readiness claim or proof that any private R&D system
works.

## Short Answer

ClaimBound is most useful in software R&D as a lightweight discipline for
important claims, not as a heavy framework around every commit, debug run or
exploratory script.

The practical rule is:

```text
Move fast without ClaimBound for exploration.
Use ClaimBound-style boundaries for claims that affect publication, roadmap,
alpha, release, production or external trust.
```

This matters because R&D language drifts quickly. A phrase such as "the signal
works", "the feature adds value", "the channel is invalid", "AUC is good" or
"we can move toward production" can mean very different things unless it is
bound to a dataset, baseline, command, artifact, metric, threshold and status.

## Why Lightweight Mode Exists

Early software R&D needs speed:

- implementation plumbing changes quickly;
- APIs and data contracts are still being discovered;
- exploratory scripts may be temporary;
- many hypotheses should die before they become formal tracks;
- forcing a full evidence card for every small step creates overhead before the
  claim is important enough to preserve.

But important R&D conclusions need discipline:

- feature-value claims affect roadmap decisions;
- baseline comparisons can change meaning after the fact;
- partial wins can be overstated as robust evidence;
- negative or blocked results can disappear into informal notes;
- production language can appear before gates have passed.

Lightweight ClaimBound use sits between those two needs. It does not require a
completed card for every experiment. It does require important claims to be
small, checkable and status-bound before they are reused.

## Example: Time-Series Indicator R&D

In a private time-series indicator R&D project, the team was iterating on
feature engineering, labels, multi-timeframe datasets and model gates. A full
public evidence card was not created for that work, so this section should be
read only as a methodology example.

The lightweight ClaimBound layer would have been useful around claims such as:

| R&D statement | Common failure mode without claim boundaries | Lightweight ClaimBound boundary |
| --- | --- | --- |
| `Direction works` | Later review may reveal that it depends on a specific rule, output buffer or preprocessing path. | Specify rule, output field, dataset, command and expected distribution before using the statement. |
| `The channel is invalid` | A zero-width channel may be invalid for one mode but expected for another. | Add a rule-specific exception and record what the channel can and cannot prove. |
| `The feature added value` | The baseline can drift from `OHLCV-only` to `OHLCV+MTF`, changing the claim. | Name the exact baseline, candidate feature set, metric, slice and gate status. |
| `AUC was good` | A high metric can come from leakage, invalid labels or non-live-safe columns. | Require leakage audit, live-safe feature list and a frozen validation split before citing it. |
| `The slow timeframe failed` | A failed candidate can be misread as rejecting the whole timeframe as context. | Mark the result as diagnostic for that candidate only, not a rejection of the entire context family. |
| `The pruned core is better` | One slice may improve while another fails a research gate. | Use `PARTIAL_DIAGNOSTIC_ONLY` until all required gates pass. |
| `Move toward production` | A predictive residual signal may be confused with tradable alpha. | Keep `production_allowed: false` until residual, robustness and after-cost execution gates pass. |

The main benefit is semantic control: the team can keep exploring quickly while
preventing an intermediate observation from becoming a broader claim.

## Lightweight Claim Record

A small R&D claim record can be enough before a full evidence card exists:

```text
claim_id:
statement:
scope:
baseline:
candidate:
dataset_or_fixture:
command_or_checklist:
artifact_or_report:
metric:
threshold_or_gate:
result:
status:
allowed_publication:
forbidden_inference:
production_allowed:
```

Example shape for a private indicator R&D claim:

```text
claim_id: EXAMPLE-INDICATOR-H4H1-PRUNED-001
statement: The pruned indicator feature set improves the selected execution
  metric over the declared multi-timeframe baseline on this tested slice.
scope: one instrument family, one parent/child timeframe pair, current frozen
  dataset only
baseline: multi-timeframe OHLCV baseline
candidate: multi-timeframe OHLCV plus pruned indicator features
dataset_or_fixture: frozen private R&D dataset reference
command_or_checklist: frozen residual-sweep command or runbook
artifact_or_report: private or sanitized report reference
metric: after-cost execution lift and residual research gate
threshold_or_gate: gate must pass before alpha language is allowed
result: partial diagnostic observation only
status: PARTIAL_DIAGNOSTIC_ONLY
allowed_publication: diagnostic wording only
forbidden_inference: no robust alpha, no production permission, no broad feature
  superiority claim
production_allowed: false
```

This record is not a card. It is a lightweight claim boundary that prevents the
team from saying more than the evidence supports.

## When To Use Lightweight ClaimBound

Use lightweight claim discipline when the statement will influence:

- public documentation;
- a roadmap decision;
- an R&D branch stop or continuation decision;
- a baseline or feature-family comparison;
- a negative, blocked or partial result that should not disappear;
- an alpha, edge, performance, release or production claim;
- an external reviewer or funder interpretation.

For these cases, even a small record is valuable because it keeps the claim
attached to source, command, artifact, baseline, metric and status.

## When Not To Use It

Do not require a ClaimBound record for every low-risk step.

| Skip full ClaimBound for | Why |
| --- | --- |
| Typo fixes and formatting | No meaningful claim is being made. |
| Disposable exploration | The branch may die before any claim is reused. |
| Early API plumbing | Contracts are still being discovered. |
| Local debugging | Speed matters more than public evidence. |
| One-off inspection commands | The output is not being published or reused as a conclusion. |
| Claims that cannot be bounded | If the source, metric or decision rule cannot be written down, the claim should stay informal. |

The point is not to slow engineering down. The point is to prevent important
statements from escaping without evidence boundaries.

## Practical Operating Rule

For software R&D, use three levels:

| Level | Use | Artifact |
| --- | --- | --- |
| No ClaimBound | Coding, plumbing, debugging, throwaway exploration. | Ordinary commits, notes or local logs. |
| Lightweight ClaimBound | Important R&D claims before a full public card exists. | Small claim record with scope, baseline, command, artifact, metric, status and forbidden inference. |
| Full Evidence Card | Public result, release gate, completed source audit, reproducibility record or externally relied-on claim. | Validated evidence-card JSON/SVG, registry entry and sanitized report. |

This hybrid mode keeps normal software development fast while making important
claims harder to exaggerate.

## Read Next

- [Software development workflow](../SOFTWARE_DEVELOPMENT_WORKFLOW.md)
- [R&D family protocol](../R_AND_D_FAMILY_PROTOCOL.md)
- [Protocol layers v2 and v3](../PROTOCOL_LAYERS_V2_V3.md)
