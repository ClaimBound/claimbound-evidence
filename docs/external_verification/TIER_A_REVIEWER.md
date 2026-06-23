# Tier A — Reviewer / Spec Pack

**VERIFY issues:** #85 (open for external closure), #89, #90, #91, #92  
**Profile:** documentation review and validator commands; no large downloads.  
**#85 time:** ~2 min after baseline via `claimbound verify starter-pack`.

Run [baseline](README.md#before-anyone-starts) first. Primary commands work on
Windows, macOS and Linux without jq or bash.

## #85 — Starter pack (#54)

**Why:** prove that starter demos run and flagship cards use honest status fields
(NASA drift belongs in `reproduction_level`, not `result_status`).

Docs: [EXTERNAL_OPERATOR_STARTER_PACK.md](../EXTERNAL_OPERATOR_STARTER_PACK.md)

**Primary path (~2 min after baseline):**

```bash
uv run claimbound verify starter-pack
```

Expected last line: `verify_starter-pack=PASS`.

<details>
<summary>Manual equivalent (if you prefer step-by-step)</summary>

```bash
uv run claimbound demo eea-source-audit
uv run claimbound demo grok-source-audit

uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json \
  --keys evidence_id result_status reproduction_level claim_boundary
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json \
  --keys evidence_id result_status reproduction_level claim_boundary
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json \
  --keys evidence_id result_status reproduction_level claim_boundary
```

Confirm: NASA drift is in `reproduction_level`, not `result_status`.

</details>

<details>
<summary>Optional shell (jq)</summary>

```bash
jq '{evidence_id,result_status,reproduction_level,claim_boundary}' \
  docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json
```

</details>

## #89 — AI boundary review (#58)

Playbook: [ISSUE_58_AI_BOUNDARY_PLAYBOOK.md](../runbooks/ISSUE_58_AI_BOUNDARY_PLAYBOOK.md)

```bash
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json \
  --keys evidence_id claim_boundary allowed_claim_sentence known_limitations
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08.json \
  --keys evidence_id claim_boundary allowed_claim_sentence known_limitations
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08.json \
  --keys evidence_id claim_boundary allowed_claim_sentence known_limitations
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07.json \
  --keys evidence_id claim_boundary allowed_claim_sentence known_limitations
```

Confirm: no safety, runtime, benchmark-superiority or deployment claims.

## #90 — API parity (#59)

Playbook: [ISSUE_59_API_PARITY_PLAYBOOK.md](../runbooks/ISSUE_59_API_PARITY_PLAYBOOK.md)

```bash
uv run claimbound validate-all
uv run claimbound inspect registry --keys registry_name card_count
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-API_PARITY_D001-2026-06-15.json \
  --keys evidence_id result_status claim_boundary runner_command
```

Expected: `validate-all` exits `0`, `card_count` is `33`. Record `git rev-parse HEAD`
in your issue comment if you use git.

## #91 — SourceProbe spec only (#60)

**Not a runtime reproduction.** Verify the design document only.

```bash
uv run claimbound verify source-probe-spec
```

Confirm: spec says probe cannot emit `PASSED_UNDER_PROTOCOL` by itself.

## #92 — Static registry spec only (#61)

**Not a UI reproduction.** Verify the design document only.

```bash
uv run claimbound verify static-registry-spec
```

Confirm: [PLANNED_NOT_SHIPPED.md](../PLANNED_NOT_SHIPPED.md) matches repository state.

## Post results

Use [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on each issue you completed.
