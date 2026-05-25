# Demo Tracks To Evidence Cards

This document defines the honest path from a public example to a real
ClaimBound card.

A demo, testimonial or scaffold is not evidence. A README example may point to a
card only after there is a request, frozen protocol, run or checklist, sanitized
report, validated JSON card and registry entry.

## Publication Rule

Publish a card as evidence only when it has one documented result status:

- `PASSED_UNDER_PROTOCOL`
- `NEGATIVE_RESULT_UNDER_PROTOCOL`
- `BLOCKED_SOURCE`
- `INSUFFICIENT_COVERAGE`
- `REPRODUCED_OUTCOME`
- `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`

Do not show `GRAY_DRAFT_NOT_EXECUTED` as evidence. It can appear only as a
request or scaffold example.

## Workflow

```text
evidence request
  -> scaffold
  -> family/frontier ledger for related tracks
  -> preregistration charter
  -> playbook and checklist
  -> manual or AI-assisted local run
  -> raw logs, transcripts or payloads outside repo
  -> public sanitized report
  -> validated evidence card JSON
  -> rendered SVG card
  -> registry update
```

## Ten Audience Categories

| Audience / category | Example track | What the card should prove | Current status |
| --- | --- | --- | --- |
| Public AI transparency readers | `GROK_PROMPTS_SOURCE_AUDIT_D001`, Anthropic/OpenAI/Google public-doc source audits | Public AI documentation source boundaries are reachable, dated, hashed and limited to source audit only. | Green cards exist for source audits. Runtime equivalence is not proven. |
| AI and LLM evaluation teams | `MODEL_EVAL_D001` | Model ID, prompt set, transcript hashes, scoring rule and acceptance gate are available before outcome scoring. | `BLOCKED_SOURCE` until those fields are available. |
| Companies with AI products | `AI_PRODUCT_CLAIM_D001` | A product claim is narrow enough to show customers without implying certification or deployment readiness. | `BLOCKED_SOURCE` until model/source docs and evidence artifacts are available. |
| Independent verifiers and public buyers | `PROCUREMENT_AI_D001` | A vendor claim has independently checkable sources, scoring and limitations before adoption. | `BLOCKED_SOURCE` until procurement-ready source and scoring evidence exists. |
| Data stewards and public-data teams | `SOURCE_AUDIT_D001`, `EEA_AQ_D001` | Official source page, rights note, data-service link and raw-payload policy are clear before coverage scoring. | EEA source audit is green; EEA AQ manual track is `BLOCKED_SOURCE` on incomplete public URL manifest; CDC mirror path remains unresolved. |
| Civic tech, journalism and watchdogs | `CIVIC_CLAIM_D001`, NYC TLC Phase 4 | A public civic claim can be resolved from official data without overclaiming. | Current cards/artifacts are blocked or negative, not success claims. |
| Open science and reproducibility teams | `REPRO_APPENDIX_D001`, NASA POWER D-103, NOAA CO-OPS D-131 | A published result can pass, fail or reproduce with drift under a fixed protocol. | NASA passed with source-byte drift; NOAA is negative; reproduction appendix is blocked. |
| ML researchers | `ML_APPENDIX_D001` | A method appendix states source, baselines, controls, gate and claim boundary. | `BLOCKED_SOURCE` until a completed run validates. |
| Educators | `EDU_REPRO_D001` | Students can learn protocol freeze, status discipline and limitation writing on public data. | `BLOCKED_SOURCE` until a classroom run is completed. |
| Funding reviewers and program evaluators | `FUNDING_REVIEW_D001` | A report or proposal has source, protocol, status and forbidden-claim boundaries. | `BLOCKED_SOURCE` until the appendix links to validated cards. |

## Scaffold Files

`uv run claimbound new` creates a draft scaffold:

```text
docs/evidence_requests/<TRACK_ID>_REQUEST.md
docs/protocols/<TRACK_ID>_PREREG_CHARTER.md
docs/manual_audit/<TRACK_ID>/<TRACK_ID>_PLAYBOOK.md
docs/manual_audit/<TRACK_ID>/<TRACK_ID>_CHECKLIST.md
docs/manual_audit/<TRACK_ID>/<TRACK_ID>_OPERATOR_DECLARATION.md
docs/evidence_card_drafts/CLAIMBOUND-<TRACK_ID>-DRAFT.json
docs/track_families/<TRACK_ID>_FAMILY_LEDGER.json
artifacts/<track_id>_source_probe_summary.json
```

Those files are a safe starting point. They are not a result.
For related R&D tracks, the family ledger is where claim IDs, proof surface,
diagnostic versus proof mode, proof-track budget, stop rules and closure
decisions are recorded. Optional frontier ledgers summarize alive, stopped and
closed family state.

## Local-Only Files

Manual and AI-assisted runs should keep sensitive or bulky material outside the
repository:

```text
$HOME/claimbound_runs/<run_id>/raw/
$HOME/claimbound_runs/<run_id>/logs/
$HOME/claimbound_runs/<run_id>/hashes/
$HOME/claimbound_runs/<run_id>/transcripts/
```

The public repository stores sanitized summaries, hashes and cards, not raw
payloads or private transcripts.

## Manual Track

Manual track:

1. Human writes the narrow claim.
2. Human freezes source, gate, scoring and stop rules.
3. Human completes the checklist.
4. Human records deviations and limitations.
5. Validator checks the card before registry publication.

Use this when judgment, source-rights review or domain interpretation is the
main risk.

For the EEA AQ D-001 manual track, the reusable runner is:

```bash
python3 scripts/claimbound_run_eea_manual_track.py \
  --probe-eea-api \
  --report artifacts/eea_aq_d001_manual_summary.json
```

The current committed card is blocked-source because the fixed API URL-list path
did not provide a complete BE/DE/NL manifest. A future operator can rerun with a
local raw-payload folder and publish a new exact status.

## AI-Assisted Track

AI-assisted track:

1. AI may draft the request, scaffold, family ledger and missing-field checks.
2. Human freezes the protocol and source boundary.
3. AI may write runner, parser, scorer or validation code.
4. Deterministic code or checklist produces the report.
5. AI may draft card wording from validated artifacts.
6. Human approves final status, claim boundary and publication.

AI must not choose favorable examples after seeing outcomes, change thresholds,
hide failures, invent hashes or approve its own final result.
