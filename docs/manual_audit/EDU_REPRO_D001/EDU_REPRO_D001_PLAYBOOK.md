# EDU_REPRO_D001 Playbook

This playbook is a scaffold. Follow it only after the protocol is reviewed and
frozen.

## Setup

```bash
uv sync --extra dev
uv run --extra dev python scripts/claimbound_validate_evidence_card.py --help
```

## Operator Flow

1. Open the public claim source: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
2. Record the exact claim being checked.
3. Freeze the protocol before collecting outcomes.
4. Create a run root outside this repository.
5. Record source rights and raw payload policy.
6. Collect local-only raw payloads, prompts, transcripts or logs.
7. Hash local-only artifacts.
8. Produce a sanitized summary in `artifacts/`.
9. Complete an evidence card JSON.
10. Run the evidence-card validator.
11. Update the registry only after validation.

## Expected Public Outputs

```text
docs/protocols/EDU_REPRO_D001_PREREG_CHARTER.md
docs/manual_audit/EDU_REPRO_D001/EDU_REPRO_D001_CHECKLIST.md
docs/evidence_cards/CLAIMBOUND-EDU_REPRO_D001-<DATE>.json
artifacts/edu_repro_d001_summary.json
```
