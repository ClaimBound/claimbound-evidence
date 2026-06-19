# External Verification Packs

Split verification work so different operators can close different VERIFY issues
without one person carrying the full load.

## Before Anyone Starts

Every operator runs the same baseline on current `main`:

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
git pull origin main

export REPO_ROOT="$(pwd)"
export OPERATOR="<github-handle>"
export TODAY="$(date +%F)"

uv sync --extra dev
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Expected: `valid_cards=24`, `72 passed`, both commands exit `0`.

## Choose A Pack

| Pack | Operator profile | VERIFY issues | Time |
| --- | --- | --- | --- |
| [Tier A — reviewer / spec](TIER_A_REVIEWER.md) | Doc review, validators, no heavy downloads | #85, #89, #90, #91, #92 | ~1 h |
| [Tier B — EEA drift](TIER_B_EEA_DRIFT.md) | Public-data probe, network | #88 | ~30 min |
| [Tier C — NASA rerun](TIER_C_NASA_RERUN.md) | Reproducibility, curl + gate | #86 | 1–2 h |
| [Tier C — NOAA rerun](TIER_C_NOAA_RERUN.md) | Reproducibility, API fetch + gate | #87 | 1–2 h |

Minimum credible external signal for reviewers: **Tier A + one Tier C pack** from
an operator who is not the maintainer.

## After Your Pack

1. Post a closing comment using [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md).
2. Check all boxes that apply to your pack.
3. Close the VERIFY issue if you have permission, or ask the maintainer to close.

Maintainers: see [MAINTAINER_TRIAGE.md](MAINTAINER_TRIAGE.md).

## Related Docs

- [External operator starter pack](../EXTERNAL_OPERATOR_STARTER_PACK.md)
- [Planned work not shipped](../PLANNED_NOT_SHIPPED.md)
- [Artifacts catalog](../artifacts/README.md) — NYC TLC / CDC are artifact-only