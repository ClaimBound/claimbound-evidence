# Issue #58 Playbook — AI source-audit boundary review

Goal: verify AI source-audit cards and docs do not overclaim model safety,
quality, runtime behavior or benchmark superiority.

This is a **wording review**. Network reruns are optional.

## Cards to review

```bash
cd "$REPO_ROOT"

CARDS=(
  CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08
  CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08
  CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08
  CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07
)

for card in "${CARDS[@]}"; do
  echo "=== $card ==="
  jq '{evidence_id, claim_boundary, allowed_claim_sentence, known_limitations}' \
    "docs/evidence_cards/${card}.json"
done
```

Also read:

```bash
open docs/CURRENT_EVIDENCE_TRACKS.md
open docs/REVIEWER_SUMMARY.md
open README.md
```

## Checklist per card

- [ ] `claim_boundary` excludes safety / quality / runtime / benchmarks
- [ ] `allowed_claim_sentence` is source-audit only
- [ ] `known_limitations` is complete
- [ ] SVG matches JSON boundary text
- [ ] README / tracks do not overclaim

## Optional fresh source probes

```bash
uv run python scripts/claimbound_run_public_doc_source_audit.py \
  --protocol-id ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001 \
  --source-name "Anthropic Model System Cards" \
  --source-url "https://www.anthropic.com/system-cards/" \
  --expect "Anthropic" --expect "Claude" --expect "System cards" \
  --claim-boundary "Source audit only." \
  --report /tmp/anthropic_boundary_check.json

uv run python scripts/claimbound_run_public_doc_source_audit.py \
  --protocol-id OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001 \
  --source-name "OpenAI GPT-5 System Card PDF" \
  --source-url "https://cdn.openai.com/gpt-5-system-card.pdf" \
  --expect "GPT" \
  --claim-boundary "Source audit only." \
  --report /tmp/openai_boundary_check.json

uv run python scripts/claimbound_run_public_doc_source_audit.py \
  --protocol-id GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001 \
  --source-name "Google DeepMind Model Cards" \
  --source-url "https://deepmind.google/models/model-cards" \
  --expect "Google" --expect "Gemini" --expect "Model cards" \
  --claim-boundary "Source audit only." \
  --report /tmp/deepmind_boundary_check.json

rm -rf /tmp/grok-prompts
git clone --depth 1 https://github.com/xai-org/grok-prompts /tmp/grok-prompts
uv run python scripts/claimbound_run_grok_prompts_source_audit.py \
  --repo-dir /tmp/grok-prompts \
  --report /tmp/grok_boundary_check.json
```

## Deliverable

```bash
mkdir -p docs/reviews

cat > "docs/reviews/AI_SOURCE_AUDIT_BOUNDARY_REVIEW_${TODAY}.md" <<'EOF'
# AI Source Audit Boundary Review

| Card | boundary OK? | docs overclaim? | fix needed? |
| --- | --- | --- | --- |
| Anthropic | | | |
| OpenAI GPT-5 | | | |
| Google DeepMind | | | |
| Grok prompts | | | |
EOF

open "docs/reviews/AI_SOURCE_AUDIT_BOUNDARY_REVIEW_${TODAY}.md"
```

If JSON wording changes:

```bash
uv run --extra dev python scripts/claimbound_render_evidence_card_svg.py \
  docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json \
  docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg

uv run claimbound validate-all
```

Closes #58.
