# Funding Eligibility Self-Check Example

This example shows how ClaimBound can be used by an applicant to check their own
public project against public funding eligibility criteria without turning the
result into a funding decision claim.

It is intentionally narrow. It does not claim that a funding organization should
fund the project, that reviewers will agree with the applicant, or that the
submitted proposal is accepted. It only shows how public rules can be converted
into bounded, reviewable claims.

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
  `INSUFFICIENT_COVERAGE`, not as a pass.

If the self-check is published after an application has already been submitted,
label it as a public applicant-side example, not as a modification of the
submitted application.

## Example Source Boundary

For a public eligibility self-check, the source boundary should be limited to
public pages such as:

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
criteria to public project facts. It does not represent any funder, programme,
review committee or funding decision. It must not be used to claim that the
project is selected, ranked, approved or more likely to be funded.
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
- completed checklist or scoring table;
- local raw-source archive or source hashes, if redistribution is allowed;
- sanitized report;
- evidence-card JSON;
- rendered SVG card;
- registry entry, if the result is published as a public card.

Do not publish private proposal text, private reviewer communication or personal
data as part of this example. If the example should stay non-branded, keep the
funder name out of committed files and store the exact source URLs only in the
local run root or sanitized source manifest.

## Local Run For A Specific Public Call

Use this workflow when you want to check ClaimBound Evidence against a specific
public eligibility page without committing private application material.

1. Install and validate the current repository.

```bash
uv sync --extra dev
uv run claimbound validate-all
```

2. Create a local-only run root. Use the exact public eligibility URL for the
   target call.

```bash
uv run claimbound run-root \
  --protocol-id FUNDING_ELIGIBILITY_SELF_CHECK_D001 \
  --source-url "https://example.org/public-call/eligibility/" \
  --operator "your-name-or-handle"
```

3. Create a local scaffold outside committed documentation.

```bash
uv run claimbound new \
  --source-url "https://example.org/public-call/eligibility/" \
  --protocol-id "FUNDING_ELIGIBILITY_SELF_CHECK_D001" \
  --domain "funding-review" \
  --track-type "source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --source-name "Public eligibility pages for the target funding call" \
  --audience "applicant-side funding reviewers" \
  --out "$HOME/claimbound_runs/FUNDING_ELIGIBILITY_SELF_CHECK_D001/scaffold"
```

4. Freeze the public source manifest before scoring:

```text
source_id,url,role,access_date,content_type,sha256_or_note
CALL_MAIN,https://example.org/public-call/,public fund page,YYYY-MM-DD,html,...
CALL_ELIGIBILITY,https://example.org/public-call/eligibility/,eligibility criteria,YYYY-MM-DD,html,...
CALL_GUIDE,https://example.org/public-call/guide/,guide for applicants,YYYY-MM-DD,html,...
CALL_FAQ,https://example.org/public-call/faq/,public FAQ,YYYY-MM-DD,html,...
PROJECT_README,https://github.com/ClaimBound/claimbound-evidence,project README,YYYY-MM-DD,html,...
PROJECT_LICENSE,https://github.com/ClaimBound/claimbound-evidence/blob/main/LICENSE,project license,YYYY-MM-DD,html,...
```

5. Score only the frozen narrow claims below. Use `PASSED_UNDER_PROTOCOL` only
   for items directly supported by public text. Use `BLOCKED_SOURCE` or
   `INSUFFICIENT_COVERAGE` when the source is unavailable, ambiguous or too broad.

| Narrow claim | Suggested status gate |
| --- | --- |
| The project repository is publicly readable at access time. | Public repository page is reachable without authentication. |
| The repository declares a recognized free/open-source license. | `LICENSE` is present and matches a recognized license. |
| The public project docs describe software, documentation, validation or quality work that can map to at least one eligible activity category. | Both the public eligibility text and project docs support the narrow mapping. |
| The project has a public-interest or commons-oriented boundary in public docs. | Public docs support the boundary without relying on private proposal text. |
| The self-check uses only public source material. | Source manifest contains only public URLs or publishable hashes. |
| The evidence boundary rejects endorsement and funding-decision claims. | Final boundary text explicitly says the card is not approval, selection, ranking or endorsement. |
| The published artifact exposes no private application or reviewer material. | Sanitized report contains no private proposal text, personal data or private communication. |

6. If you publish a real card, render and validate it before adding it to the
   registry:

```bash
uv run python scripts/claimbound_validate_evidence_card.py \
  docs/evidence_cards/CLAIMBOUND-FUNDING-ELIGIBILITY-SELF-CHECK-D001-YYYY-MM-DD.json

uv run python scripts/claimbound_render_evidence_card_svg.py \
  docs/evidence_cards/CLAIMBOUND-FUNDING-ELIGIBILITY-SELF-CHECK-D001-YYYY-MM-DD.json \
  docs/evidence_cards/CLAIMBOUND-FUNDING-ELIGIBILITY-SELF-CHECK-D001-YYYY-MM-DD.svg

uv run claimbound validate-all
```

Until those steps are completed, this file remains a public runbook and example,
not a completed eligibility result.
