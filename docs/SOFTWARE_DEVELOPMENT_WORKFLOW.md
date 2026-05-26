# Software Development Workflow

Status: guidance and scaffold. This page is not a completed evidence record.

ClaimBound can support software development when a change needs a small public
evidence trail: the narrow claim, the frozen rule, the commands or checklist
used, the result status, and the boundary of what the result does not prove.

It is not a replacement for unit tests, integration tests, CLI commands, CI,
manual QA, code review, release engineering, security review, maintainer
judgment or ordinary project quality practices. ClaimBound records and explains
selected checks; it does not become the checks.

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

The evidence card should answer one question only:

```text
What exactly was checked, by which fixed procedure, at which commit, and what
must readers not infer from the result?
```

A green software-development card means one narrow software claim passed under
one written protocol. It does not mean the whole project is correct, secure,
complete, stable or deployment-ready.

## When It Fits

Use ClaimBound for complex, risky, public, AI-assisted or regression-sensitive
software changes. Do not use a full track for every typo, formatting edit, small
comment or disposable prototype.

Good fit examples:

- public pull requests that change behavior users rely on;
- crash, data-loss, migration, compatibility or regression fixes;
- AI-assisted patches that need deterministic verification;
- compatibility, parity or regression checks with fixed fixtures;
- local API, CLI or library behavior checks summarized with sanitized logs and hashes;
- interactive or manual workflows where a checklist is needed because no unit
  test covers the scenario yet;
- build-system, packaging or platform-compatibility changes where environment
  details matter;
- R&D sequences where diagnostic, proof, reproduction and closure tracks must
  not be confused.

## Practical Advantages

| Development problem | ClaimBound contribution |
| --- | --- |
| Broad claims such as `the feature works` | Converts the statement into one or more narrow, testable claims. |
| Regression risk | Records the exact commands, fixtures, logs, environment notes and limitations. |
| AI-assisted patches | Separates code generation from deterministic runner or checklist results. |
| Public PR review | Shows what was checked, what was not checked and what is still risky. |
| Hard-to-automate behavior | Allows a manual checklist while keeping the result bounded and auditable. |
| Negative or blocked outcomes | Keeps failures useful instead of renaming them as success. |
| Repeated R&D attempts | Uses family ledgers, stop rules and closure records to avoid selective reruns. |
| Cross-platform uncertainty | Makes OS, compiler, runtime and fixture boundaries explicit. |
| Long logs | Replaces log dumping with a short evidence summary plus hashes and retained artifacts. |

## Examples Of Narrow Software Claims

ClaimBound is most useful when vague engineering language is rewritten as small
claims that can pass, fail, block or remain insufficient.

| Vague statement | Better ClaimBound claim |
| --- | --- |
| `The feature works.` | `The feature command returns exit code 0 and writes the expected output for fixture set A on commit X.` |
| `The crash is fixed.` | `The documented reproduction path completes without process crash or fatal log marker on the declared local environment.` |
| `The API is compatible.` | `Endpoint A returns the same response schema for fixture requests F001-F010 as the frozen baseline, except for documented field B.` |
| `The refactor is safe.` | `The refactored module preserves the frozen public behavior for the listed fixtures and passes the existing test suite.` |
| `The AI patch is good.` | `The AI-assisted patch passes the fixed runner, does not modify forbidden files and leaves the declared regression checks green.` |
| `The CLI works.` | `The CLI command `tool subcommand --fixture fixtures/basic.json` exits 0 and emits the frozen stdout markers.` |
| `Performance improved.` | `The benchmark command completes the fixed workload at least N% faster than the baseline on the declared machine, without changing output hashes.` |

Good claims are small, environment-bound and falsifiable. Weak claims are broad,
subjective or deployment-like.

## Example Track Patterns

### Regression or crash fix

```text
Claim 1: The project builds on the declared local environment.
Claim 2: The existing test suite remains green.
Claim 3: The documented reproduction path no longer crashes.
Claim 4: The sanitized log contains no fatal marker for the tested path.
Claim 5: The fix does not disable the feature or remove the entry point.
Claim 6: The result is limited to the declared OS, build type, commit and fixtures.
```

This is useful when a bug is easy to describe but hard to prove globally. The
card should say `passed under this path`, not `bug eliminated everywhere`.

### API, library or CLI behavior

```text
Claim 1: The command or endpoint is invoked with a frozen fixture set.
Claim 2: Exit code, response schema, stdout markers or output hashes match the gate.
Claim 3: Known unsupported arguments, inputs or platforms are listed as limitations.
Claim 4: The result comes from the command, test or validator, not from AI opinion.
```

This is useful for public packages, tools, data pipelines and local services.

### Refactor, migration or compatibility work

```text
Claim 1: The old and new implementations produce matching output for frozen fixtures.
Claim 2: The existing unit and integration tests still pass.
Claim 3: Any intentional output differences are listed before scoring.
Claim 4: The card does not claim full semantic equivalence outside the fixtures.
```

This is useful when the main risk is preserving behavior while changing internals.

### AI-assisted patch

```text
Claim 1: The AI-assisted change is limited to declared files or modules.
Claim 2: The generated code passes the fixed runner or checklist.
Claim 3: The patch does not remove asserts, disable checks or hide errors unless that is the explicit frozen claim.
Claim 4: A human maintainer approves final status and boundary wording.
```

This is useful because AI can write plausible code while still missing the real
engineering boundary.

## What ClaimBound Does Not Replace

ClaimBound must stay outside the normal quality stack. It can cite or summarize
ordinary checks, but it must not replace them.

It does not replace:

- unit tests;
- integration tests;
- end-to-end tests;
- property tests or fuzz tests;
- CLI commands and local verification scripts;
- CI workflows and build matrices;
- compiler warnings, linters, type checkers or formatters;
- code review;
- maintainer judgment;
- manual QA;
- security review, threat modeling or penetration testing;
- release engineering and rollback planning;
- production monitoring and incident response;
- documentation review.

The correct relationship is:

```text
Unit tests / CI / CLI / review decide engineering quality.
ClaimBound records one narrow evidence claim about selected checks and their limits.
```

## Where ClaimBound Should Not Be Applied

Do not use a full ClaimBound track when the overhead is larger than the risk or
when the claim cannot be made narrow and checkable.

Usually not worth it:

- typo fixes;
- formatting-only changes;
- comment-only edits;
- small rename-only patches;
- disposable local experiments;
- private scratch prototypes that will not become a PR;
- purely subjective preference changes;
- one-off debugging notes that will not be reused.

Wrong or dangerous uses:

- claiming the whole project is correct because one evidence card is green;
- claiming production readiness from a local-only check;
- claiming security certification without an external security review process;
- turning subjective judgment into a fake objective result after seeing output;
- using a card to bypass tests, CI or review;
- hiding negative, blocked or insufficient results;
- changing thresholds, fixtures or acceptance gates after seeing the result;
- using vague claims such as `fixed`, `works`, `safe`, `ready` or `secure`
  without a frozen boundary.

## Fit Levels

| Fit level | Examples | Recommended use |
| --- | --- | --- |
| Strong fit | crash fixes, regression-sensitive behavior, public API changes, migrations, AI-assisted patches, cross-platform compatibility, R&D proof tracks | Use a full ClaimBound track with claims, commands/checklist, artifacts and limitations. |
| Moderate fit | UI behavior, build packaging, developer tooling, documentation examples with executable snippets | Use a short evidence summary or a lightweight track when the change is public or risky. |
| Weak fit | style-only edits, comments, renames, exploratory prototypes | Do not use ClaimBound unless the change becomes a public or risky claim. |
| Not appropriate | broad correctness, security certification, production readiness, subjective quality claims | Split into narrow claims or use ordinary engineering/governance processes instead. |

## Recommended PR Evidence Summary

A software PR should stay readable. The public PR does not need a huge evidence
bundle when a compact summary is enough.

Good PR evidence summary:

```text
Claim:
- Narrow behavior, build, API, parity or regression claim.

Checked:
- Commit and branch.
- Commands or manual checklist.
- Fixture set or scenario.
- Sanitized log/report path.
- Result status.

Passed:
- Existing tests or selected command outputs.
- Fixed runner/checklist result.

Not checked:
- Other platforms.
- Other build modes.
- Larger input corpus.
- Production deployment.
- Security properties.
```

This helps maintainers review the change without pretending the evidence card is
a replacement for ordinary project review.

## Universal Protocol Use

The same ClaimBound layers can support one software check or a larger development sequence:

- an evidence card records one completed command, fixture, checklist or validator result;
- a family ledger can hold a one-track claim list, proof surface, stop rule and closure boundary;
- a frontier ledger can summarize runnable, stopped or closed development work when useful;
- a v3 tree overlay can start as one node and later expand to many nodes with iron claims, flow claims and tombstones.

These layers are optional helpers around normal engineering practice. They do
not replace the project's tests, CI, review or release process.

## Workflow

```text
software claim
  -> evidence request
  -> narrow claim list
  -> protocol freeze
  -> implementation or patch
  -> deterministic tests, CLI command, CI result or manual checklist
  -> sanitized report and hashes
  -> validated evidence card
  -> optional independent rerun or closure
```

The result must come from a command, test, checklist, validator or reviewed CI
result, not from AI opinion.

## Generic Draft Example

Draft question:

```text
Can this software-development track produce a protocol-bound evidence record for one narrow behavior, compatibility, parity or regression claim, using fixed commands, fixtures, sanitized logs, hashes and a boundary that does not claim deployment readiness or correctness outside the protocol?
```

The draft evidence card should stay gray until a real run produces validated
artifacts. A completed card may be green, amber, red or yellow depending on what
happened.
