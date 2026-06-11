# SOFTWARE_DEV_D001 Playbook

Frozen protocol for a software-development validator regression gate.

## Setup

```bash
uv sync --extra dev
```

## Operator Flow

1. Confirm `docs/protocols/SOFTWARE_DEV_D001_PREREG_CHARTER.md` is frozen.
2. Record repository commit hash.
3. Run the frozen pytest gate command.
4. Confirm expected violation string for missing `execution_mode`.
5. Run `uv run claimbound validate-all`.
6. Write `artifacts/software_dev_d001_summary.json`.
7. Complete evidence card JSON and render SVG from JSON.
8. Update registry only after validation passes.

## Frozen Commands

```bash
uv run --extra dev python -m pytest tests/test_evidence_card.py::test_evidence_card_requires_execution_mode -q
uv run claimbound validate-all
```

## Expected Public Outputs

```text
docs/protocols/SOFTWARE_DEV_D001_PREREG_CHARTER.md
docs/manual_audit/SOFTWARE_DEV_D001/
artifacts/software_dev_d001_summary.json
docs/evidence_cards/CLAIMBOUND-SOFTWARE_DEV_D001-<DATE>.json
```
