# Software Development Workflow

Status: guidance and scaffold. This page is not a completed evidence record.

ClaimBound can support software development when a change needs a small public evidence trail: the narrow claim, the frozen rule, the commands or checklist used, the result status, and the boundary of what the result does not prove.

It is not a replacement for tests, CI, code review, release engineering, maintainer judgment or ordinary project quality practices.

## When It Fits

Use ClaimBound for complex, risky, public, AI-assisted or regression-sensitive software changes. Do not use a full track for every typo, formatting edit, small comment or disposable prototype.

Good fit examples:

- public pull requests that change behavior users rely on;
- AI-assisted patches that need deterministic verification;
- compatibility, parity or regression checks with fixed fixtures;
- local API or library behavior checks summarized with sanitized logs and hashes;
- R&D sequences where diagnostic, proof, reproduction and closure tracks must not be confused.

## What It Adds

| Development problem | ClaimBound contribution |
| --- | --- |
| Broad claims such as "the feature works" | Converts the claim into narrow, testable statements. |
| Regression risk | Records commands, fixtures, logs and limitations. |
| AI-assisted patches | Separates generated code from deterministic runner or checklist results. |
| Public PR review | Shows what was checked and what was not checked. |
| Negative or blocked outcomes | Keeps failures useful instead of renaming them as success. |
| Repeated R&D attempts | Uses family ledgers, stop rules and closure records to avoid selective reruns. |

## Limits

A green software-development card means only that one narrow claim passed under one written protocol. It does not mean the whole project is correct, complete or ready for deployment.

ClaimBound must not be presented as:

- a replacement for software tests;
- proof of correctness outside the protocol boundary;
- proof of production readiness unless that is a separate frozen claim;
- a way to make subjective judgments look objective after the result is known;
- a certification service unless an external review process exists.

## Universal Protocol Use

The same ClaimBound layers can support one software check or a larger development sequence:

- an evidence card records one completed command, fixture, checklist or validator result;
- a family ledger can hold a one-track claim list, proof surface, stop rule and closure boundary;
- a frontier ledger can summarize runnable, stopped or closed development work when useful;
- a v3 tree overlay can start as one node and later expand to many nodes with iron claims, flow claims and tombstones.

These layers are optional helpers around normal engineering practice. They do not replace the project's tests, CI, review or release process.

## Workflow

```text
software claim
  -> evidence request
  -> narrow claim list
  -> protocol freeze
  -> implementation or patch
  -> deterministic tests or manual checklist
  -> sanitized report and hashes
  -> validated evidence card
  -> optional independent rerun or closure
```

The result must come from a command, test, checklist or validator, not from AI opinion.

## Generic Draft Example

Draft question:

```text
Can this software-development track produce a protocol-bound evidence record for one narrow behavior, compatibility, parity or regression claim, using fixed commands, fixtures, sanitized logs, hashes and a boundary that does not claim deployment readiness or correctness outside the protocol?
```

The draft evidence card should stay gray until a real run produces validated artifacts. A completed card may be green, amber, red or yellow depending on what happened.
