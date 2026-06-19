# Tier A — Reviewer / Spec Pack

**VERIFY issues:** #85, #89, #90, #91, #92  
**Profile:** documentation review and validator commands; no large downloads.

Run [baseline](README.md#before-anyone-starts) first.

## #85 — Starter pack (#54)

Docs: [EXTERNAL_OPERATOR_STARTER_PACK.md](../EXTERNAL_OPERATOR_STARTER_PACK.md)

```bash
cd "$REPO_ROOT"

uv run claimbound demo eea-source-audit
uv run claimbound demo grok-source-audit

jq '{evidence_id,result_status,reproduction_level,claim_boundary}' \
  docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json
jq '{evidence_id,result_status,reproduction_level,claim_boundary}' \
  docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json
jq '{evidence_id,result_status,reproduction_level,claim_boundary}' \
  docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json
```

Confirm: NASA drift is in `reproduction_level`, not `result_status`.

## #89 — AI boundary review (#58)

Playbook: [ISSUE_58_AI_BOUNDARY_PLAYBOOK.md](../runbooks/ISSUE_58_AI_BOUNDARY_PLAYBOOK.md)

```bash
cd "$REPO_ROOT"

for card in \
  CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08 \
  CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08 \
  CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08 \
  CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07
do
  echo "=== $card ==="
  jq '{evidence_id, claim_boundary, allowed_claim_sentence, known_limitations}' \
    "docs/evidence_cards/${card}.json"
done
```

Confirm: no safety, runtime, benchmark-superiority or deployment claims.

## #90 — API parity (#59)

Playbook: [ISSUE_59_API_PARITY_PLAYBOOK.md](../runbooks/ISSUE_59_API_PARITY_PLAYBOOK.md)

```bash
cd "$REPO_ROOT"

export GIT_SHA="$(git rev-parse HEAD)"

uv run python scripts/claimbound_validate_registry.py
echo "validate_registry_exit=$?"

uv run claimbound validate-all
echo "validate_all_exit=$?"

jq '{registry_name, card_count}' docs/registry/evidence_index.json
jq '{evidence_id,result_status,claim_boundary,runner_command}' \
  docs/evidence_cards/CLAIMBOUND-API_PARITY_D001-2026-06-15.json
```

Expected: both exits `0`, `card_count=24`.

## #91 — SourceProbe spec only (#60)

**Not a runtime reproduction.** Verify the design document only.

```bash
cd "$REPO_ROOT"

head -8 docs/SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md
test ! -e scripts/claimbound_source_probe.py
grep -n "design document" docs/SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md
```

Confirm: spec says probe cannot emit `PASSED_UNDER_PROTOCOL` by itself.

## #92 — Static registry spec only (#61)

**Not a UI reproduction.** Verify the design document only.

```bash
cd "$REPO_ROOT"

head -8 docs/STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md
test ! -e scripts/claimbound_build_registry_view.py
test ! -d docs/registry/views
```

Confirm: [PLANNED_NOT_SHIPPED.md](../PLANNED_NOT_SHIPPED.md) matches repository state.

## Post results

Use [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on each issue you completed.