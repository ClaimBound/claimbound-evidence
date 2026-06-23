# Artifact-Only Records

This catalog lists sanitized summaries and proof-path outputs that are **not**
validated evidence cards.

Reviewers: the public registry at [evidence_index.json](../registry/evidence_index.json)
contains **40** validated cards only. NYC TLC Phase 4 and CDC mirror path appear
here as transparency artifacts, not as missing registry entries by mistake.

## Card versus artifact versus scaffold

| Type | In public registry? | Status semantics | Example |
| --- | --- | --- | --- |
| **Evidence card** | Yes | Exact `result_status` under frozen protocol | Anthropic source audit |
| **Artifact-only** | No | Run completed; card fields incomplete | NYC TLC Phase 4 summary |
| **Scaffold** | No | Gray / not executed | `claimbound new` draft output |

Artifacts can be useful for transparency, but they must not be cited as completed
evidence cards until they have protocol, source boundary, sanitized artifact,
exact status, claim boundary, reproduction level and a registry entry.

## Current artifact-only records

| Artifact | File | Outcome | Why not a card yet |
| --- | --- | --- | --- |
| NYC TLC Phase 4 | [NYC TLC negative result](../evidence/NYC_TLC_PHASE4_NEGATIVE_RESULT.md) | Negative run completed | No validated card JSON/SVG in registry |
| NYC TLC Phase 4 summary | [artifacts/nyc_tlc_phase4_negative_result_summary.json](../../artifacts/nyc_tlc_phase4_negative_result_summary.json) | Negative artifact | Summary only |
| CDC mirror path | [CDC mirror source boundary](../evidence/CDC_MIRROR_SOURCE_BOUNDARY.md) | Blocked-source style | External source equivalence unresolved |
| CDC mirror summary | [artifacts/cdc_mirror_source_boundary_summary.json](../../artifacts/cdc_mirror_source_boundary_summary.json) | Blocked artifact | Summary only |

## Related blocked cards (validated, not artifacts)

The [civic claim card](../evidence_cards/CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json)
for NYC TLC is a **validated blocked-source card** (`BLOCKED_SOURCE`). It is
different from the NYC TLC Phase 4 artifact: the card records a narrow civic
claim boundary; the artifact records an empirical run without full card promotion.

## Promotion path

To promote an artifact to a card:

1. Freeze a protocol charter.
2. Run the check under fixed gates.
3. Publish sanitized summary + hashes only.
4. Validate card JSON and update [registry](../registry/evidence_index.json).
5. Run `uv run claimbound validate-all`.

Until then, cite artifacts only as artifact-only records with explicit limits.
