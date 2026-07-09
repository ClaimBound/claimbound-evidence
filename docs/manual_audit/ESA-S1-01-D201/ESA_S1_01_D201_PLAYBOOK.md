# ESA_S1_01_D201 Playbook

This playbook is a scaffold. Follow it only after the protocol is reviewed and
frozen.

## Setup

```bash
uv sync --extra dev
uv run --extra dev python scripts/claimbound_validate_evidence_card.py --help
uv run claimbound validate-tree docs/track_families/ESA_S1_01_D201_TREE.json
```

## Operator Flow

1. Open the public claim source: https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1
2. Record the exact claim being checked.
3. Freeze the protocol before collecting outcomes.
4. Create a run root outside this repository.
5. Record source rights and raw payload policy.
6. Collect local-only raw payloads, prompts, transcripts or logs.
7. Hash local-only artifacts.
8. Produce a sanitized summary in `artifacts/`.
9. Complete an evidence card JSON.
10. Run the evidence-card validator.
11. Validate optional family, frontier or v3 tree overlays when present.
12. Update the registry only after validation.

## Expected Public Outputs

```text
docs/protocols/ESA_S1_01_D201_PREREG_CHARTER.md
docs/manual_audit/ESA_S1_01_D201_CHECKLIST.md
docs/track_families/ESA_S1_01_D201_TREE.json
docs/evidence_cards/CLAIMBOUND-ESA_S1_01_D201-<DATE>.json
artifacts/esa_s1_01_d201_summary.json
```
