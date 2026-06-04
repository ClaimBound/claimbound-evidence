# Funding Eligibility Self-Check Example

This example shows how ClaimBound can be used by an applicant to check their own
public project against public funding eligibility criteria without turning the
result into a funding decision claim.

It is intentionally narrow. It does not claim that a funding organization should fund the
project, that reviewers will agree with the applicant, or that the submitted
proposal is accepted. It only shows how public rules can be converted into
bounded, reviewable claims.

## Why This Example Exists

Funding applications often contain broad statements:

```text
This project is open source, public-interest oriented and eligible for the call.
```

ClaimBound rewrites that into smaller checks:

```text
The public repository declares a recognized open-source license.
The project description maps to at least one public eligible activity.
The self-check uses only public eligibility text and public project facts.
The evidence card does not claim funding approval, reviewer endorsement or private
application correctness.
```

That is the difference between self-promotion and evidence discipline.

## Ethical Boundary

A funding self-check is acceptable only if it stays inside these limits:

- Use public call pages, public repository facts and public project documents.
- Do not imply endorsement by the funding organization.
- Do not claim that the submitted proposal is selected, ranked or approved.
- Do not rewrite history after submission.
- Do not include private reviewer communication, private application text or
  personal data unless there is a clear reason and permission to publish it.
- Treat uncertain, missing or ambiguous items as `BLOCKED_SOURCE` or
  `INSUFFICIENT_SOURCE`, not as a pass.

If the self-check is published after an application has already been submitted,
label it as a public applicant-side example, not as a modification of the
submitted application.

## Example Source Boundary

For an NLnet-style public eligibility self-check, the source boundary should be
limited to public pages such as:

- the public fund page;
- the public eligibility page;
- the public guide for applicants;
- the public FAQ;
- the public repository README, license and evidence documents.

The self-check must not rely on private email, assumptions about reviewers or
unpublished proposal text.

## Candidate Narrow Claims

| Candidate claim | Evidence source | Honest status rule |
| --- | --- | --- |
| The project repository is publicly readable. | Repository URL and metadata. | Pass only if the repository is public at access time. |
| The repository declares a recognized open-source license. | `LICENSE`, `pyproject.toml`, README badge or package metadata. | Pass only if the license is visible and recognized; otherwise block. |
| The project work maps to eligible activity categories such as free/open-source software, validation, documentation, usability or software-quality work. | Public eligibility page and public project docs. | Pass only for the specific categories supported by text; do not claim complete eligibility. |
| The project has a public-interest or commons-oriented boundary. | Fund page, README, audience/value docs. | Mark as partial or insufficient if the public docs are too vague. |
| The self-check is independent from the funding organization. | Evidence card boundary text. | Must explicitly say "not an endorsement, not a funding decision". |
| The check does not expose private application material. | Published artifact review. | Pass only if no private application text or personal data is included. |

## Minimal Evidence Card Shape

```json
{
  "claim_id": "CLAIMBOUND-FUNDING-ELIGIBILITY-SELF-CHECK-D001",
  "claim": "A public applicant-side self-check can map public funding eligibility rules to narrow ClaimBound evidence claims without claiming funding approval.",
  "status": "TEMPLATE_ONLY",
  "source_boundary": [
    "Public fund page",
    "Public eligibility page",
    "Public guide for applicants",
    "Public FAQ",
    "Public repository README and license"
  ],
  "must_not_claim": [
    "funding approval",
    "reviewer endorsement",
    "selection likelihood",
    "private proposal correctness",
    "legal or tax advice"
  ],
  "reproduction_level": "template_only_until_operator_run"
}
```

## Example Workflow

1. Freeze the public source list and access date.
2. Freeze the narrow claim list before scoring the project.
3. Record source URLs, content type and hashes where possible.
4. Check each candidate claim against public text only.
5. Mark unsupported items as blocked or insufficient.
6. Publish a sanitized report and an evidence card.
7. Add a clear limitation: this is not a funding decision.

## Good Final Boundary Text

```text
This evidence card is an applicant-side public self-check. It maps public call
criteria to public project facts. It does not represent NLnet, NGI0, any review
committee or any funding decision. It must not be used to claim that the project
is selected, ranked, approved or more likely to be funded.
```

## Why This Is A Useful Adoption Example

This is a simple demonstration because a reader does not need to understand ML,
benchmarks or AI model behavior. They only need to compare:

- public rule;
- public project fact;
- narrow claim;
- exact status;
- limitation.

That makes it a good first example for funding reviewers, maintainers and
public-interest readers.

## What Would Make It A Real Card

This document is only an example until an operator creates and validates the
actual artifacts:

- frozen protocol file;
- source manifest;
