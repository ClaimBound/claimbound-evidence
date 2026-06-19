# External Verification Packs

Independent operators close open VERIFY issues to show that ClaimBound works
outside the maintainer's machine. You are **not** certifying models, approving
deployments or making program-sponsor claims — you only confirm that the published checklist
and commands reproduce on your environment.

**Who may close #85–#87:** any GitHub user who is **not** the maintainer
(`NeoZorK` / `ClaimBound` bot bootstrap runs do not count as external signal).

## Can you finish in 5 minutes?

| Situation | Realistic time | Can close issue? |
| --- | --- | --- |
| First visit (clone + `uv sync` + baseline) | **15–25 min** | Yes, after baseline |
| Repo already cloned, deps installed | **5–10 min per pack** | Yes |
| Tier C NASA/NOAA with `claimbound verify` shortcuts | **~1–2 min** pack run + baseline | Yes (#86, #87) |

Five minutes is enough **only when the repository is already set up**. First-time
operators should budget **15 minutes minimum** ([Start without coding](../START_WITHOUT_CODING.md)).

## Before Anyone Starts

Every operator runs the same baseline on current `main`. Works on Windows,
macOS and Linux — no jq or bash required for primary commands. See
[platform support](../PLATFORM_SUPPORT.md).

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
git pull origin main

uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Note your GitHub handle and today's date for issue comments. `claimbound doctor`
prints `today=YYYY-MM-DD`.

Expected: `ready=yes`, `valid_cards=24`, `86 passed`, all commands exit `0`.

Record `git rev-parse HEAD` for your closing comment.

## Choose A Pack

| Pack | Why it exists | VERIFY issues | One-command check | Time (after setup) |
| --- | --- | --- | --- | --- |
| [Tier A — starter](TIER_A_REVIEWER.md) | Confirm demos + flagship card semantics | **#85** | `uv run claimbound verify starter-pack` | ~2 min |
| [Tier C — NASA rerun](TIER_C_NASA_RERUN.md) | Confirm positive gate reruns independently | **#86** | `uv run claimbound verify nasa-rerun --operator <handle>` | ~1–2 min |
| [Tier C — NOAA rerun](TIER_C_NOAA_RERUN.md) | Confirm negative gate stays negative | **#87** | `uv run claimbound verify noaa-rerun --operator <handle>` | ~1–2 min |

**Minimum credible external signal:** close **#85** plus **one of #86 or #87**
from a non-maintainer operator.

**Open for independent closure:** VERIFY #85, #86, #87. Maintainer bootstrap
comments on closed mirrors are not sufficient — post a new closing comment with
your handle and today's date.

## Close An Issue (step by step)

1. Run [baseline](#before-anyone-starts) on current `main`.
2. Run the pack one-command check from the table above (replace `<handle>` with
   your GitHub username or a short handle).
3. Copy [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) into the VERIFY
   issue; fill every section; paste command output or `verify_*=PASS` lines.
4. Close the issue if you have permission, or ask the maintainer to close after
   reviewing your comment.

## Related Docs

- [External operator starter pack](../EXTERNAL_OPERATOR_STARTER_PACK.md)
- [Planned work not shipped](../PLANNED_NOT_SHIPPED.md)
- [Artifacts catalog](../artifacts/README.md) — NYC TLC / CDC are artifact-only

Maintainers: see [MAINTAINER_TRIAGE.md](MAINTAINER_TRIAGE.md).