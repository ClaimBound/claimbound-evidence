# Audience Demonstration Workflows

These are scenario testimonials, not endorsements from real users and not
completed evidence cards. They show how each audience category would use
ClaimBound through both a manual track and an AI-assisted track.

Each workflow ends with a validated evidence card or with an honest draft,
blocked, negative or limited-reproducibility status.

The concrete path from these scenarios to real cards is defined in
[demo tracks to evidence cards](DEMO_TRACKS_TO_EVIDENCE_CARDS.md). A README
example should link to a card only after the track has been run and validated.

## 1. Public AI Transparency Readers

Scenario:

```text
We see a public AI documentation claim and need to know what source evidence is
actually checkable.
```

Manual track:

1. Write the exact public documentation claim.
2. Freeze the official source URL, access date and required markers.
3. Record content type, byte size and SHA-256.
4. State what the source audit does not prove about runtime behavior.
5. Publish the card only after validation.

AI-assisted track:

1. AI drafts source-audit fields and expected markers.
2. Human freezes the source boundary.
3. Deterministic HTTP or repository checks produce the report.
4. Validator rejects model-quality, safety or deployment overclaims.
5. Human approves the final claim boundary.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.com/official-ai-doc" \
  --protocol-id "AI_TRANSPARENCY_SOURCE_AUDIT_D001" \
  --domain "ai-transparency" \
  --track-type "public_doc_source_audit" \
  --execution-mode "AUTOMATED_AI_ASSISTED" \
  --out "docs/manual_audit/AI_TRANSPARENCY_SOURCE_AUDIT_D001"
```

## 2. AI And LLM Evaluation Teams

Scenario:

```text
We need to check whether a model, RAG system or agent claim has reproducible
evidence instead of a screenshot or leaderboard sentence.
```

Manual track:

1. Write the exact model claim.
2. Freeze prompt set, model id, settings, source rule and scoring rule.
3. Record prompt hash or Merkle root before answer collection.
4. Run the model and save transcripts outside the repo.
5. Hash transcripts and scorer script.
6. Score deterministically.
7. Publish evidence card with pass, negative, blocked or limited status.

AI-assisted track:

1. AI drafts protocol and checks required fields.
2. Human freezes protocol.
3. Automated runner collects answers.
4. Deterministic scorer writes report.
5. Validator rejects missing hashes, broad claims or undisclosed AI use.
6. Human approves claim boundary.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.org/model-claim" \
  --protocol-id "MODEL_EVAL_D001" \
  --domain "ai-model-evaluation" \
  --track-type "model_benchmark_claim" \
  --execution-mode "AUTOMATED_AI_ASSISTED" \
  --out "docs/manual_audit/MODEL_EVAL_D001"
```

## 3. Open Science And Reproducibility Researchers

Scenario:

```text
We tried to reproduce a paper result. The result did not pass, but the failure
is useful and should be citable.
```

Manual track:

1. Record paper/report claim.
2. Freeze reproduction protocol and allowed deviations.
3. Record source, code version, environment and data-rights boundary.
4. Run reproduction.
5. Hash logs and sanitized report.
6. Publish `reproduction_attempt` or negative result.

AI-assisted track:

1. AI extracts claimed method and missing fields.
2. Human confirms protocol and source access.
3. AI prepares runner/checklist.
4. Deterministic scripts produce report.
5. Human records deviations and final limitation.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.org/paper-or-artifact" \
  --protocol-id "REPRO_APPENDIX_D001" \
  --domain "open-science" \
  --track-type "reproduction" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/REPRO_APPENDIX_D001"
```

## 4. Funding Reviewers And Program Evaluators

Scenario:

```text
We need to see what was promised, what source was used, what happened, and what
cannot be claimed.
```

Manual track:

1. Read proposal or report claim.
2. Map claim to protocol, source, status and limitations.
3. Check whether raw data policy and source rights are visible.
4. Confirm result status is exact.
5. Read evidence card instead of a narrative success claim.

AI-assisted track:

1. AI extracts claim/protocol/status fields from submitted materials.
2. Validator checks card completeness and forbidden claims.
3. Human reviewer inspects source boundary and limitation wording.
4. Result is accepted, queried or rejected as unsupported.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.org/funding-result" \
  --protocol-id "FUNDING_REVIEW_D001" \
  --domain "funding-review" \
  --track-type "evidence_appendix" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/FUNDING_REVIEW_D001"
```

## 5. Data Stewards And Public-Data Teams

Scenario:

```text
We maintain or reuse public data. Before a performance claim, source rights,
coverage and raw payload policy must be clear.
```

Manual track:

1. Identify official source owner and docs.
2. Record license, terms, attribution and redistribution notes.
3. Check coverage, timestamps, units and file format.
4. Decide whether raw payloads can be committed.
5. Publish `source_audit` card.

AI-assisted track:

1. AI collects candidate docs and OpenAPI/CSV/JSON links.
2. Human verifies rights and official-source status.
3. Source probe writes summary.
4. Validator rejects legal overclaims and missing rights notes.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.org/public-data-docs" \
  --protocol-id "SOURCE_AUDIT_D001" \
  --domain "public-data" \
  --track-type "source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/SOURCE_AUDIT_D001"
```

## 6. Civic Tech, Journalism And Watchdogs

Scenario:

```text
A public claim about infrastructure, mobility, climate or government service
quality needs a transparent source-bound check.
```

Manual track:

1. Rewrite the public statement as a narrow claim.
2. Choose official public source and resolution period.
3. Freeze metric, scoring rule and stop conditions.
4. Run source audit or result check.
5. Publish card with limitations and no deployment claim.

AI-assisted track:

1. AI drafts candidate protocol and source list.
2. Human rejects weak or unofficial sources.
3. Runner or checklist executes fixed rule.
4. Validator blocks broad political or causal claims.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.gov/open-data" \
  --protocol-id "CIVIC_CLAIM_D001" \
  --domain "civic-tech" \
  --track-type "public_source_claim" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/CIVIC_CLAIM_D001"
```

## 7. ML Researchers

Scenario:

```text
We need a compact appendix that separates a narrow result from broad
model-superiority language.
```

Manual track:

1. Freeze method, source, baselines, controls and gate.
2. Run experiment once under protocol.
3. Record negative controls and baseline summary.
4. Publish evidence card with exact result status.

AI-assisted track:

1. AI drafts appendix fields and missing checks.
2. Human confirms no thresholds changed after outcome.
3. Automated validation checks broad-claim fragments.
4. Human approves final claim boundary.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.org/research-method" \
  --protocol-id "ML_APPENDIX_D001" \
  --domain "ml-research" \
  --track-type "research_method_appendix" \
  --execution-mode "AUTOMATED_AI_ASSISTED" \
  --out "docs/manual_audit/ML_APPENDIX_D001"
```

## 8. Educators

Scenario:

```text
Students should learn reproducible ML discipline, not only leaderboard chasing.
```

Manual track:

1. Students freeze a small protocol before seeing outcomes.
2. They run source audit or scoring checklist.
3. They publish pass, negative, blocked or insufficient coverage.
4. They explain limitations and forbidden claims.

AI-assisted track:

1. AI prepares draft checklist and starter code.
2. Students review and freeze the protocol.
3. Deterministic scripts run.
4. Validator checks evidence card.
5. Instructor reviews final claim boundary.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.edu/course-dataset" \
  --protocol-id "EDU_REPRO_D001" \
  --domain "education" \
  --track-type "teaching_reproducible_ml" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/EDU_REPRO_D001"
```

## 9. Companies With AI Products

Scenario:

```text
We want customers to see narrow evidence for a public claim instead of a broad
marketing promise.
```

Manual track:

1. Rewrite product claim as narrow public claim.
2. Freeze source, model version, prompt set and scoring rule.
3. Record operator and date.
4. Run test and publish card with limitations.
5. Avoid certification or deployment-readiness claims.

AI-assisted track:

1. AI creates protocol draft and card template.
2. Human legal/product owner narrows the claim.
3. Runner collects evidence.
4. Validator rejects marketing language.
5. Human approves public release.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.com/product-claim" \
  --protocol-id "AI_PRODUCT_CLAIM_D001" \
  --domain "ai-product-evidence" \
  --track-type "product_claim_check" \
  --execution-mode "AUTOMATED_AI_ASSISTED" \
  --out "docs/manual_audit/AI_PRODUCT_CLAIM_D001"
```

## 10. Independent Verifiers, Procurement Teams And Public Buyers

Scenario:

```text
Before adopting or buying an AI system, we need a narrow evidence record that
another operator can rerun or challenge.
```

Manual track:

1. Submit evidence request.
2. Verifier rewrites the vendor claim narrowly.
3. Verifier freezes protocol and source rule.
4. Verifier runs manual or scripted check.
5. Procurement team reads card status and limitations.

AI-assisted track:

1. AI drafts request classification and protocol.
2. Human verifier freezes source and scoring rule.
3. Runner executes and hashes artifacts.
4. Validator produces pass/fail/blocked status.
5. Independent verifier reruns if decision risk is high.

Scaffold:

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://example.com/vendor-ai-claim" \
  --protocol-id "PROCUREMENT_AI_D001" \
  --domain "public-procurement" \
  --track-type "procurement_claim_check" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/PROCUREMENT_AI_D001"
```

## Common Card Outcomes

Every audience uses the same status discipline:

- `PASSED_UNDER_PROTOCOL`: the narrow claim passed the frozen gate only.
- `NEGATIVE_RESULT_UNDER_PROTOCOL`: the claim was tested and did not pass.
- `BLOCKED_SOURCE`: source, rights, access, scoring or model metadata blocked a
  fair run.
- `INSUFFICIENT_COVERAGE`: source exists but cannot support the frozen gate.
- `REPRODUCED_OUTCOME` or `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`: another
  operator reproduced the status or gate outcome.

Validity color is separate from result status:

- green means evidence is complete enough to rerun;
- yellow means limited reproducibility;
- red means invalid or tamper evidence;
- gray means draft, request or scaffold only.
