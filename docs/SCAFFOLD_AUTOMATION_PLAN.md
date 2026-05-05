# Scaffold Automation Plan

This document describes the next practical automation step for ClaimBound.

The goal is to generate a track scaffold from a public source description
without producing an unsupported result.

A scaffold is not evidence by itself. It is a prepared workspace for a future
operator run.

## Goal

Create a command that can prepare:

- source probe summary;
- protocol draft;
- playbook;
- checklist;
- operator declaration;
- evidence card draft;
- validation notes.

The scaffold should help an operator avoid missing required evidence steps.

## Non-Goals

The scaffold must not:

- claim that a result passed;
- choose thresholds after inspecting outcomes;
- hide source problems;
- fabricate hashes;
- commit external payloads;
- replace human review for source rights and claim boundary;
- produce broad model-superiority claims.

## Proposed Command

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.org/source-docs" \
  --protocol-id "EXAMPLE_D001" \
  --domain "public-data" \
  --track-type "source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/EXAMPLE_D001"
```

## Proposed Outputs

```text
docs/protocols/EXAMPLE_D001_PREREG_CHARTER.md
docs/manual_audit/EXAMPLE_D001_PLAYBOOK.md
docs/manual_audit/EXAMPLE_D001_CHECKLIST.md
docs/manual_audit/EXAMPLE_D001_OPERATOR_DECLARATION.md
docs/evidence_cards/CLAIMBOUND-EXAMPLE-D001-DRAFT.json
artifacts/example_d001_source_probe_summary.json
```

## Suggested Modules

| Module | Purpose |
| --- | --- |
| SourceProbe | Checks whether the source URL, documentation, API, table or file endpoint is readable. |
| RightsProbe | Records license, terms, attribution and redistribution notes without making a legal conclusion. |
| TrackClassifier | Suggests a track type such as source audit, time-series signal, forecast resolution or reproduction. |
| ProtocolDraftBuilder | Creates a preregistration charter with fixed placeholders for source, target, baselines, controls and gates. |
| ChecklistRenderer | Creates a step-by-step checklist with commands, expected artifacts and stop conditions. |
| PlaybookRenderer | Creates a human-readable runbook for the operator. |
| EvidenceCardScaffolder | Creates a draft card without a positive or negative result status. |
| CardValidator | Ensures that the final evidence card uses allowed fields and does not overclaim. |
| RegistryPatchBuilder | Prepares a registry patch only after the evidence card validates. |
| SvgRenderer | Renders SVG from validated JSON instead of hand-editing the visual card. |

## Source Probe Minimum

A source probe should record:

- source name;
- source URL;
- access date;
- HTTP status or access result;
- content type;
- documentation URL when available;
- license or terms link when available;
- whether external payloads may be committed;
- coverage notes;
- unresolved source-boundary questions.

## Checklist Minimum

A generated checklist should include:

- [ ] Source URL opens.
- [ ] Official documentation or source owner is identified.
- [ ] Rights and attribution note is recorded.
- [ ] Payload policy is recorded.
- [ ] Protocol file exists before the run.
- [ ] Target is fixed before the run.
- [ ] Candidate method is fixed before the run.
- [ ] Baselines are fixed before the run.
- [ ] Negative controls are fixed before the run.
- [ ] Acceptance gate is fixed before the run.
- [ ] Stop conditions are listed.
- [ ] External payload hashes or manifest are recorded outside the repository.
- [ ] Sanitized public artifact is created.
- [ ] Evidence card validates.
- [ ] Registry entry is added only after validation.

## Draft Card Rule

A scaffolded draft card should not contain `PASSED_UNDER_PROTOCOL` or
`NEGATIVE_RESULT_UNDER_PROTOCOL`.

Before execution, it should use a draft-only marker outside the official
result-status list, or omit `result_status` until a real run is completed.

## Test Plan

Add tests that verify:

- scaffold creates all expected files;
- draft card does not claim a result;
- payload policy defaults to not committed;
- checklist includes stop conditions;
- generated files contain no broad claims;
- final cards still pass the deterministic evidence-card validator.

## Recommended Implementation Order

1. Add static templates.
2. Add a deterministic scaffold command.
3. Add source-probe summary output.
4. Add draft evidence-card generation.
5. Add validation tests.
6. Add one example scaffold for an air-quality source.
