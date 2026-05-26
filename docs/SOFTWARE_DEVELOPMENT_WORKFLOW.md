# Software Development Workflow

Status: guidance and scaffold. This page is not a completed evidence record.

ClaimBound can support software development when a change needs a small public evidence trail: the narrow claim, the frozen rule, the commands or checklist used, the result status, and the boundary of what the result does not prove.

It is not a replacement for tests, CI, code review, release engineering, maintainer judgment or ordinary project quality practices.

## When It Fits

Use ClaimBound for complex, risky, public, AI-assisted or regression-sensitive software changes. Do not use a full track for every typo, formatting edit, small comment or disposable prototype.

## What It Adds

| Development problem | ClaimBound contribution |
| --- | --- |
| Broad claims such as "the feature works" | Converts the claim into narrow, testable statements. |
| Regression risk | Records commands, fixtures, logs and limitations. |
| AI-assisted patches | Separates generated code from deterministic runner or checklist results. |
| Public PR review | Shows what was checked and what was not checked. |
| Negative or blocked outcomes | Keeps failures useful instead of renaming them as success. |

## Limits

A green software-development card means only that one narrow claim passed under one written protocol. It does not mean the whole project is correct, complete or ready for deployment.

ClaimBound must not be presented as a replacement for software tests, proof of correctness outside the protocol boundary, or proof of production readiness unless that is a separate frozen claim.

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
