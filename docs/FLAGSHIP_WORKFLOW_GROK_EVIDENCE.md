# Flagship Workflow: Where Is The Evidence?

ClaimBound should make one public habit simple:

```text
Before trusting a public AI, ML or data claim, ask for the evidence card.
```

This document uses a Grok prompt-transparency claim as a worked example. It is
a completed source-audit example for the public `xai-org/grok-prompts`
repository. It does not verify Grok model quality or live runtime equivalence.

## Correct Workflow

A ClaimBound track has five distinct states. Do not skip them.

```text
1. Evidence request
   A public claim is submitted with source URL, audience, proposed source and
   scoring rule. This is only a request.

2. Scaffold
   ClaimBound creates draft protocol, playbook, checklist and draft evidence
   card. This is still not evidence.

3. Protocol freeze
   A human operator reviews and freezes repository URL, required files,
   manifest fields, pass gate, stop conditions and forbidden claims before
   collecting source metadata.

4. Execution
   Manual or AI-assisted track clones or reads the public repository at a fixed
   commit, hashes prompt files, creates a sanitized report and records
   deviations. Prompt text is not committed here.

5. Validated card
   Validator checks required fields and forbidden claims. The final card is
   green, yellow, red, gray, blocked, negative or reproduced according to the
   actual artifacts.
```

For the Grok prompt-transparency example, scaffold creates the request and draft
track. The green card requires an actual source audit run.

To create a real card, the operator must also have:

- access to the public `xai-org/grok-prompts` repository;
- a frozen repository URL and pass gate;
- a fixed commit hash;
- README and LICENSE checks;
- a prompt file hash manifest;
- a sanitized source-audit report;
- a validator-passing evidence card.

If any of those are missing, the honest outcome is not green.

## Public Claim Source

xAI's public `grok-prompts` repository says it is regularly updated with system
prompts used for the Grok chat assistant and product features across X and
grok.com.

Useful source pages:

- xAI Grok prompts repository:
  <https://github.com/xai-org/grok-prompts>
- xAI Grok 4 API docs:
  <https://docs.x.ai/developers/models/grok-4>
- xAI Grok 4 model card:
  <https://data.x.ai/2025-08-20-grok-4-model-card.pdf>

The ClaimBound question is not:

```text
Does this prove exactly what prompt the free Grok 4 chat fast runtime uses?
```

That is too broad.

The ClaimBound question is:

```text
Can the public prompt-disclosure source boundary be verified with repository
commit, README/license presence, prompt file list and SHA-256 hashes?
```

## README-Ready Example

```text
Public claim: xAI publishes Grok system prompts in the public xai-org/grok-prompts
repository.

ClaimBound status today: green source-audit card exists in this repository.

Why green is allowed: this card checks only public repository source boundary,
commit identity, README/license presence and prompt file hashes. It does not
claim live runtime equivalence.

ClaimBound output now: PASSED_UNDER_PROTOCOL / GREEN_VALIDATED source audit.

Card: docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json
Visual card: docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.svg
```

## Narrow Protocol

Protocol ID:

```text
GROK_PROMPTS_SOURCE_AUDIT_D001
```

Claim boundary:

```text
This record checks only whether the public xai-org/grok-prompts repository is
available at a fixed commit with README, LICENSE and prompt-file SHA-256
manifest. It does not prove that a live Grok runtime uses those exact prompts,
that hidden server-side layers are absent, or that Grok is superior outside this
protocol.
```

Allowed source types:

- official xAI GitHub repository;
- repository README;
- repository LICENSE;
- prompt files listed in the public repository;
- git commit hash.

Required source metadata:

```text
repository_url:
remote_url:
head_commit:
readme_present:
license_present:
prompt_file_count:
prompt_file_hash_manifest:
raw_prompt_text_committed: false
```

## Manual Track

Manual track is for a human operator who reviews the public repository and
confirms the source boundary before accepting the card.

1. Record the public claim source.
2. Record repository URL and expected owner.
3. Freeze pass gate: canonical remote, non-empty commit, README present,
   LICENSE present and at least one prompt file hash.
4. Clone or inspect the repository at a fixed commit.
5. Record commit hash.
6. Confirm README and LICENSE presence.
7. Hash prompt files by path, byte size and SHA-256.
8. Commit no prompt text into ClaimBound.
9. Create sanitized source-audit report.
10. Validate evidence card.
11. Publish exact status and claim boundary.

Manual stop conditions:

- repository cannot be accessed;
- repository owner or remote URL is not the expected public source;
- README or LICENSE is missing;
- no prompt files are present;
- prompt file hashes cannot be recorded;
- the operator would need to claim live runtime equivalence.

## AI-Assisted Track

AI assistance is allowed only to prepare and check artifacts. It must not decide
that the claim passed.

Allowed AI tasks:

- draft protocol fields before source metadata is collected;
- inspect whether required fields are missing;
- generate source-audit runner boilerplate;
- summarize machine-readable source-audit reports;
- draft evidence-card wording from validated data.

Prohibited AI tasks:

- choose favorable questions after seeing answers;
- change pass gates after seeing source metadata;
- hide missing files;
- fabricate commits, hashes, sources or license notes;
- mark the final card green by narrative judgment;
- convert a blocked or negative result into a positive claim.

AI-assisted workflow:

1. AI prepares scaffold from the public claim source.
2. Human reviews and freezes protocol.
3. Runner executes source audit and writes prompt hash manifest.
4. Runner writes machine-readable report.
5. Validator checks card fields and forbidden claims.
6. Human operator approves final claim boundary.
7. Independent operator reruns if possible.

## Anti-Cheating Controls

Use these controls for prompt-source transparency:

- fixed git commit;
- canonical remote URL;
- README and LICENSE presence checks;
- prompt file path, byte size and SHA-256 manifest;
- no prompt text copied into this repository;
- no runtime-equivalence claim;
- no post-result pass-gate changes;
- validator rejects broad claims;
- independent rerun produces `reproduction_attempt`;
- card color reflects evidence strength, not marketing or votes.

## Scaffold Example

This is the intended scaffold shape. A generated draft must not claim a result.

```bash
uv run python scripts/claimbound_scaffold_track.py \
  --source-url "https://github.com/xai-org/grok-prompts" \
  --protocol-id "GROK_PROMPTS_SOURCE_AUDIT_D001" \
  --domain "ai-transparency" \
  --track-type "prompt_source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --out "docs/manual_audit/GROK_PROMPTS_SOURCE_AUDIT_D001"
```

Expected draft outputs:

```text
docs/protocols/GROK_PROMPTS_SOURCE_AUDIT_D001_PREREG_CHARTER.md
docs/manual_audit/GROK_PROMPTS_SOURCE_AUDIT_D001_PLAYBOOK.md
docs/manual_audit/GROK_PROMPTS_SOURCE_AUDIT_D001_CHECKLIST.md
docs/evidence_card_drafts/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-DRAFT.json
artifacts/grok_prompts_source_audit_d001_source_probe_summary.json
```

Draft card status:

```text
PASSED_UNDER_PROTOCOL / GREEN_VALIDATED after source audit execution
```

The draft became green only after a real source-audit run produced the sanitized
report and evidence card. The green card is limited to source transparency and
does not prove live Grok runtime equivalence.

## Local Rerun Check

The Grok source-audit workflow was rerun from a fresh local clone of
`xai-org/grok-prompts`. The sanitized report hash matched the original report:

```text
2bd2558bff930977062932d8a04290309e1e92a0ee7750aad64c42342e58a8a7
```

Rerun report:

```text
artifacts/grok_prompts_source_audit_d001_local_rerun_summary.json
```

This is a workflow sanity check, not an independent reproduction claim. A
separate operator and environment should create a `reproduction_attempt` card
before the reproduction level is upgraded.
