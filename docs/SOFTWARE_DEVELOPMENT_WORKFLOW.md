# Software Development Workflow

Status: guidance with one completed example card.

Completed example (validator regression gate under frozen pytest commands):

<p>
  <img
    src="evidence_cards/CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.svg"
    alt="ClaimBound SOFTWARE_DEV_D001 evidence card"
    width="75%"
  />
</p>

[CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11](evidence_cards/CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json) ·
[SVG](evidence_cards/CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.svg)

## Where ClaimBound Was Used Here

This repository ships two linked software examples:

| Layer | Where | How ClaimBound was used |
| --- | --- | --- |
| In-repo card | [SOFTWARE_DEV_D001](protocols/SOFTWARE_DEV_D001_PREREG_CHARTER.md) | Frozen protocol, fixed pytest gate, `validate-all`, sanitized summary hash, validated JSON/SVG card and registry entry. |
| External case study | [software-rnd-evidence-case-study](case_studies/SOFTWARE_RND_EVIDENCE_CASE_STUDY.md) | Same evidence-chain discipline on a private multi-protocol R&D track: protocol → run → report → negative/blocked record, with explicit NO-GO track closure. |

### In-repo use (SOFTWARE_DEV_D001)

**Where:** evidence-card validator regression in this repository.

**How:**

1. Pre-registered charter froze one narrow claim before the run.
2. Operator ran fixed commands only:
   `pytest tests/test_evidence_card.py::test_evidence_card_requires_execution_mode`
   and `claimbound validate-all`.
3. Sanitized summary went to `artifacts/software_dev_d001_summary.json` with SHA-256.
4. Card JSON/SVG and registry entry recorded exact status, limitations and forbidden interpretations.

**Why:** the project needed a public, reviewable proof that the validator still
rejects a card missing `execution_mode` — not a vague “tests are green” story.

**What it gave:** a third party can see the exact gate, commit context, hash and
boundary without reading the whole test suite or inferring deployment readiness.

### External use (software R&D case study)

**Where:** a private time-series R&D program, published later as a sanitized static export.

**How:** Hardgate A/B protocol ladder, negative/blocked YAML records, closure
docs and an explicit tombstone when replication candidates stayed at zero.

**Why:** utility R&D often overclaims from early deltas. ClaimBound-style rules
forced frozen protocols, first-class negative records and honest track closure.

**What it gave:** a public methodology example that shows NO-GO and BLOCKED
outcomes as useful evidence instead of silent continuation or marketing upgrade.

## Why ClaimBound — Strengths For Software Work

| Strength | What it means in practice |
| --- | --- |
| Narrow claims | Replaces `works`, `fixed`, `ready` with one falsifiable sentence. |
| Frozen protocol | Rules and gates are fixed before the run; thresholds cannot drift after results. |
| Exact status | `PASSED`, `NEGATIVE`, `BLOCKED` and `INSUFFICIENT` stay distinct. |
| Claim boundary | Every card states what must **not** be inferred from a green result. |
| Evidence chain | protocol → dataset/command → run → report/hash → card or negative record. |
| Negative results stay visible | Failures and blocked domains remain first-class, not deleted or reframed. |
| Thin layer over engineering | Records selected checks; does not replace tests, CI, review or security work. |
| Public review surface | JSON, SVG, registry and sanitized artifacts are shareable without raw payloads. |

For this repository, the card above is green only for one validator regression
gate. It is not proof that the whole toolkit, CI or any external R&D program is
production-ready.

## What Would Change Without ClaimBound

Without this discipline, the same work would likely look like ordinary engineering
documentation:

| Without ClaimBound | Typical failure mode |
| --- | --- |
| `pytest` green only | Readers assume full validator coverage or project correctness. |
| README success narrative | A small Mission1 delta can be marketed as overall utility success. |
| No frozen protocol | Gates move after seeing results; selective reruns look like progress. |
| No negative records | BLOCKED domains and NO-GO tracks disappear into “future work”. |
| No claim boundary | Reviewers, funders or users infer endorsement, safety or readiness. |
| No hashed sanitized report | “We checked it” has no stable artifact to compare later. |
| No registry card | The check is not discoverable, citable or independently rerunnable. |

ClaimBound does not make software correct. It makes **what was checked, under
which limits, with which outcome** hard to exaggerate later.

## Core Principle

Use ClaimBound as a thin evidence layer around normal software engineering:

```text
ordinary engineering work
+ frozen narrow claim
+ fixed command/checklist path
+ sanitized logs and hashes
+ exact status
+ explicit limitations
= reviewable evidence record
```

A green software-development card means one narrow software claim passed under
one written protocol. It does not mean the whole project is correct, secure,
complete, stable or deployment-ready.

For AI-assisted changes, see [12 AI Life Rules](TWELVE_AI_LIFE_CONTROLS.md).

ClaimBound is not a replacement for unit tests, integration tests, CLI, CI,
manual QA, code review, release engineering or security review.

## When It Fits

Use ClaimBound for complex, risky, public, AI-assisted or regression-sensitive
software changes — including R&D sequences where proof, reproduction and closure
must not be confused.

Do not use a full track for typo fixes, formatting-only edits or disposable
prototypes.

## Practical Advantages

| Development problem | ClaimBound contribution |
| --- | --- |
| Broad claims such as `the feature works` | Converts the statement into narrow, testable claims. |
| Regression risk | Records exact commands, fixtures, logs and limitations. |
| AI-assisted patches | Separates code generation from deterministic runner results. |
| Public PR review | Shows what was checked, what was not checked and what remains risky. |
| Negative or blocked outcomes | Keeps failures useful instead of renaming them as success. |
| Repeated R&D attempts | Uses stop rules and closure records to avoid selective reruns. |

## Examples Of Narrow Software Claims

| Vague statement | Better ClaimBound claim |
| --- | --- |
| `The feature works.` | `The feature command returns exit code 0 for fixture set A on commit X.` |
| `The crash is fixed.` | `The documented reproduction path completes without crash on the declared environment.` |
| `The AI patch is good.` | `The AI-assisted patch passes the fixed runner and leaves declared regression checks green.` |

More track patterns: [TRACK_PATTERN_EXAMPLES.md](software_development/TRACK_PATTERN_EXAMPLES.md).

## What ClaimBound Does Not Replace

Unit tests, integration tests, CI, linters, code review, maintainer judgment,
manual QA, security review, release engineering and production monitoring.

```text
Tests / CI / review decide engineering quality.
ClaimBound records one narrow evidence claim about selected checks and their limits.
```

## Where ClaimBound Should Not Be Applied

Do not use a full track when overhead exceeds risk or the claim cannot be narrow
and checkable. Do not claim whole-project correctness, production readiness or
security certification from one green card.

## Fit Levels

| Fit level | Examples | Recommended use |
| --- | --- | --- |
| Strong fit | crash fixes, API changes, AI-assisted patches, R&D proof tracks | Full track with claims, commands, artifacts and limitations. |
| Moderate fit | build packaging, executable doc examples | Lightweight summary when public or risky. |
| Weak fit | style-only edits, exploratory prototypes | Skip unless the change becomes a public claim. |

## Recommended PR Evidence Summary

```text
Claim: narrow behavior, build, API, parity or regression claim.
Checked: commit, commands/checklist, fixtures, sanitized report path, status.
Passed: selected tests or command outputs.
Not checked: other platforms, build modes, production deployment, security.
```

## Workflow

```text
software claim
  -> evidence request
  -> narrow claim list
  -> protocol freeze
  -> implementation or patch
  -> deterministic tests, CLI, CI or manual checklist
  -> sanitized report and hashes
  -> validated evidence card
  -> optional independent rerun or closure
```

The result must come from a command, test, checklist, validator or reviewed CI
result — not from AI opinion.
