# ClaimBound In 5 Minutes

ClaimBound turns a public claim into a small evidence card.

If there is no evidence card, the statement is still only a claim.

![ClaimBound workflow](assets/claimbound_workflow.svg)

## The Idea

People make public claims about AI systems, models, datasets and methods. A
ClaimBound card asks whether one narrow version of that claim was checked under
rules fixed before the result.

The card records:

- the exact claim;
- the public source;
- the frozen protocol;
- the result status;
- the hashes and sanitized report;
- the boundary: what the card proves and what it does not prove.

ClaimBound is not a leaderboard, certification authority, newsroom, raw-data
archive or blockchain project. It is a thin evidence layer between a claim and a
public source.

## One Simple AI Example

Public claim:

```text
Anthropic publishes a public system-card index for its AI models.
```

ClaimBound question:

```text
Can the official Anthropic system-card page be source-audited by URL, access
date, content type, expected markers and SHA-256?
```

Card status:

```text
PASSED_UNDER_PROTOCOL
```

Allowed interpretation:

```text
The public source page passed the documented source-audit gate at access time.
```

Forbidden interpretation:

```text
This does not prove model safety, model quality, runtime behavior, deployment
readiness or benchmark superiority.
```

That boundary is the point. A useful card can be green without becoming a broad
endorsement.

## Statuses In Plain Language

| Status | Plain meaning |
| --- | --- |
| `PASSED_UNDER_PROTOCOL` | It passed, but only under the written rules. |
| `NEGATIVE_RESULT_UNDER_PROTOCOL` | It was tested and did not pass. |
| `BLOCKED_SOURCE` | The source, access, metadata or rights boundary blocked a fair result. |
| `INSUFFICIENT_COVERAGE` | The source exists, but there is not enough usable coverage. |
| `REPRODUCED_OUTCOME` | Another run reproduced the status or gate-level outcome. |
| `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` | The outcome reproduced, but fresh source bytes differed. |

Negative, blocked and drift cards are useful. They stop weak claims from being
renamed as successes.

## The Workflow

1. Write a narrow public claim.
2. Open an evidence request.
3. Generate a scaffold: protocol draft, playbook, checklist and draft card.
4. Freeze source, scoring, gate and stop rules before outcome inspection.
5. Run a manual checklist or deterministic script.
6. Keep raw payloads, prompt text and transcripts outside the public repo.
7. Publish a sanitized report with hashes and limitations.
8. Validate the evidence card JSON.
9. Add it to the registry only after validation.

## Where To Start

- Browse the [evidence cards](evidence_cards/README.md).
- Follow [getting started](GETTING_STARTED.md) for installation and commands.
- Use `uv run claimbound new` to create a scaffold.
- Use `uv run claimbound validate-all` before publishing cards.
