# ClaimBound In 5 Minutes

ClaimBound turns a public claim into a small evidence card.

If there is no evidence card, the statement is still only a claim.

![ClaimBound workflow](assets/claimbound_workflow.svg)

## What It Is

ClaimBound is a public evidence-card toolkit for narrow AI, ML and data claims.
It records:

- what was claimed;
- which public source was used;
- which rules were fixed before the result;
- what happened under those rules;
- what must not be claimed beyond that boundary.

The point is not to say "trust this model" or "trust this project". The point is
to make the evidence trail small enough to inspect.

## What It Is Not

ClaimBound is not:

- a model leaderboard;
- a production forecasting service;
- a certification authority;
- a fact-checking newsroom;
- a raw-data archive;
- a blockchain or token project.

It is a thin evidence layer between a public claim and a public source.

## One Example

Public claim:

```text
xAI publishes system prompts for Grok in a public repository.
```

ClaimBound narrows it:

```text
Can the public prompt-disclosure source boundary be verified with repository
commit, README/LICENSE presence and prompt-file hashes without copying prompt
text into this repository?
```

Evidence card status:

```text
PASSED_UNDER_PROTOCOL
```

What the card proves:

```text
The public repository source-audit gate passed for the documented commit,
metadata and prompt-file hash manifest.
```

What it does not prove:

```text
It does not prove live runtime equivalence, hidden-layer absence, model safety,
model quality or benchmark superiority.
```

## Statuses In Plain Language

| Status | Plain meaning |
| --- | --- |
| `PASSED_UNDER_PROTOCOL` | It passed, but only under the written rules. |
| `NEGATIVE_RESULT_UNDER_PROTOCOL` | It was honestly tested and did not pass. |
| `BLOCKED_SOURCE` | The source did not allow a fair evidence record. |
| `INSUFFICIENT_COVERAGE` | There was not enough usable data or coverage. |
| `REPRODUCED_OUTCOME` | Another run reproduced the outcome. |
| `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | The outcome matched, but fresh source bytes differed. |

Negative and blocked cards are useful. They stop weak claims from being renamed
as successes.

## The Short Workflow

1. Write a narrow public claim.
2. Open an evidence request.
3. Generate a scaffold: protocol draft, playbook, checklist and draft card.
4. Freeze source, scoring, gate and stop rules before outcome inspection.
5. Run a manual checklist or deterministic script.
6. Keep raw payloads outside the public repository.
7. Publish a sanitized report with hashes and limitations.
8. Create an evidence card JSON.
9. Validate the card and registry.
10. Add the result to the registry only after validation.

## Where To Start

- Read the current cards in [evidence cards](evidence_cards/README.md).
- Open a request using the GitHub evidence request template.
- Use `uv run claimbound new` to create a scaffold.
- Use `uv run claimbound validate-all` before publishing cards.
