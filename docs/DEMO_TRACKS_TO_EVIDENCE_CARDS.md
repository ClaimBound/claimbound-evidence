# Demo Tracks To Evidence Cards

This document defines the honest path from a scenario testimonial to a real
ClaimBound card.

It exists because a testimonial is not enough. A README example should point to
a validated card only after a request, scaffold, protocol, run, report and
validator pass exist.

## Card Publication Rule

Do not put a demo card in the README as evidence unless it has one of these:

- `PASSED_UNDER_PROTOCOL`;
- `NEGATIVE_RESULT_UNDER_PROTOCOL`;
- `BLOCKED_SOURCE`;
- `INSUFFICIENT_COVERAGE`;
- `REPRODUCED_OUTCOME`;
- `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`.

Do not show `GRAY_DRAFT_NOT_EXECUTED` as evidence. It can appear only as a
request or scaffold example.

## Full Workflow

Every demo track must follow the same path:

```text
request example
  -> scaffold command
  -> preregistration charter
  -> playbook
  -> checklist
  -> manual or AI-assisted local run
  -> raw logs/transcripts/payloads outside repo
  -> public sanitized report
  -> validated evidence card JSON
  -> optional SVG card
  -> registry update
  -> README link only after validation
```

## Ten Demo Tracks

| Track ID | Audience | Honest local outcome target | README rule |
| --- | --- | --- | --- |
| `GROK_PROMPTS_SOURCE_AUDIT_D001` | Public AI transparency / flagship workflow | `PASSED_UNDER_PROTOCOL` for repository source audit when commit, README, license and prompt hashes validate. Local rerun report matches the original sanitized-report hash, but independent reproduction is still pending. | Show as green only for prompt-source audit, not runtime equivalence. |
| `MODEL_EVAL_D001` | AI and LLM evaluation teams | Public model-card or benchmark-claim readiness audit: are model id, prompt set, scoring rule and transcript hashes available? | Show only after prompt manifest, transcript hashes and score report validate. |
| `REPRO_APPENDIX_D001` | Open science / reproducibility | Independent rerun of an existing public ClaimBound card, starting with NASA POWER D-103. | Show reproduced, negative or source-byte-drift status honestly. |
| `FUNDING_REVIEW_D001` | Funding reviewers | Evidence appendix audit for a public report: promised protocol, source, result status and forbidden claims. | Show source/status/limitations trail, not funding strategy. |
| `SOURCE_AUDIT_D001` | Data stewards | EEA Air Quality source-readiness audit: official source, rights, coverage, raw payload policy. | Show `source_audit`, blocked or source-ready status. |
| `CIVIC_CLAIM_D001` | Civic tech / journalism | NYC TLC public-data claim readiness: can a civic mobility claim be resolved from official data without raw redistribution? | Show pass/negative/blocked only. |
| `ML_APPENDIX_D001` | ML researchers | NASA POWER method-appendix card: fixed source, baselines, controls and claim boundary. | Show narrow result, not broad superiority. |
| `EDU_REPRO_D001` | Educators | Classroom reproducibility exercise using public NASA POWER source and an honest checklist. | Show as classroom reproducibility example. |
| `AI_PRODUCT_CLAIM_D001` | Companies with AI products | Public AI product transparency card: what exact public claim, model/source docs and limitations can be shown to customers? | Show only with forbidden claims listed. |
| `PROCUREMENT_AI_D001` | Independent verifiers / procurement | Procurement-readiness card for AI vendor claims: what is independently checkable before adoption? | Show as decision-support evidence, not certification. |

## Required Artifacts Per Track

Each completed demo track should create:

```text
docs/protocols/<TRACK_ID>_PREREG_CHARTER.md
docs/manual_audit/<TRACK_ID>_PLAYBOOK.md
docs/manual_audit/<TRACK_ID>_CHECKLIST.md
docs/evidence_card_drafts/CLAIMBOUND-<TRACK_ID>-DRAFT.json
docs/evidence_cards/CLAIMBOUND-<TRACK_ID>-<DATE>.json
docs/evidence_cards/CLAIMBOUND-<TRACK_ID>-<DATE>.svg
artifacts/<track_id>_summary.json
```

External local-only artifacts should stay outside the repository:

```text
$HOME/claimbound_runs/<run_id>/raw/
$HOME/claimbound_runs/<run_id>/logs/
$HOME/claimbound_runs/<run_id>/hashes/
$HOME/claimbound_runs/<run_id>/transcripts/
```

## Request Example Shape

Each track should start with an issue-like request:

```text
Title: [Evidence request]: <short claim>
Public claim:
Claim source URL:
Narrow ClaimBound question:
Main audience:
Preferred track: MANUAL_NO_AI | AUTOMATED_AI_ASSISTED
Proposed official or public sources:
Proposed scoring or resolution rule:
Known reproducibility risks:
Claims this card must not make:
```

## Local Manual Run Shape

Manual local run:

```text
1. Create run root outside the repo.
2. Freeze protocol before source outcome inspection.
3. Record source rights and raw payload policy.
4. Run checklist exactly.
5. Hash local-only raw files, transcripts or logs.
6. Write sanitized summary JSON.
7. Fill evidence card.
8. Run card validator.
9. Add registry entry only after validation.
```

## Local AI-Assisted Run Shape

AI-assisted local run:

```text
1. AI prepares scaffold and missing-field checks.
2. Human freezes protocol.
3. AI may generate runner/scorer code.
4. Deterministic runner/scorer produces report.
5. AI may draft card text from report.
6. Validator checks fields and forbidden claims.
7. Human approves final claim boundary.
```

AI must not:

- choose favorable examples after seeing outcomes;
- change thresholds after scoring;
- hide failed answers or rows;
- invent hashes, source notes, request IDs or citations;
- approve its own final status.

## Grok Track: Correct Interpretation

For `GROK_PROMPTS_SOURCE_AUDIT_D001`, the useful public claim is prompt-source
transparency, not model benchmark performance.

The green card can say:

```text
xAI's public grok-prompts repository was accessible at commit X; README and
LICENSE were present; listed prompt files were hashed; prompt text was not
copied into this repository.
```

The green card must not say:

```text
the live Grok chat runtime uses exactly these prompts;
there are no hidden prompt or policy layers;
Grok is safer, better or benchmark-superior;
the free Grok chat fast UI exposes an immutable model id.
```

## README Inclusion Rule

README should eventually show:

```text
Track ID | Audience | Status | Card | What it proves | What it does not prove
```

But only after cards validate. Until then, README should link only to the Grok
workflow and audience workflow docs as examples of how to create evidence, not
as completed evidence.
