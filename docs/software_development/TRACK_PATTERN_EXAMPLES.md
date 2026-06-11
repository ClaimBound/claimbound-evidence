# Software Track Pattern Examples

Companion patterns for [Software Development Workflow](../SOFTWARE_DEVELOPMENT_WORKFLOW.md).

## Regression or crash fix

```text
Claim 1: The project builds on the declared local environment.
Claim 2: The existing test suite remains green.
Claim 3: The documented reproduction path no longer crashes.
Claim 4: The sanitized log contains no fatal marker for the tested path.
Claim 5: The fix does not disable the feature or remove the entry point.
Claim 6: The result is limited to the declared OS, build type, commit and fixtures.
```

## API, library or CLI behavior

```text
Claim 1: The command or endpoint is invoked with a frozen fixture set.
Claim 2: Exit code, response schema, stdout markers or output hashes match the gate.
Claim 3: Known unsupported arguments, inputs or platforms are listed as limitations.
Claim 4: The result comes from the command, test or validator, not from AI opinion.
```

## Refactor, migration or compatibility work

```text
Claim 1: The old and new implementations produce matching output for frozen fixtures.
Claim 2: The existing unit and integration tests still pass.
Claim 3: Any intentional output differences are listed before scoring.
Claim 4: The card does not claim full semantic equivalence outside the fixtures.
```

## AI-assisted patch

```text
Claim 1: The AI-assisted change is limited to declared files or modules.
Claim 2: The generated code passes the fixed runner or checklist.
Claim 3: The patch does not remove asserts, disable checks or hide errors unless that is the explicit frozen claim.
Claim 4: A human maintainer approves final status and boundary wording.
```
