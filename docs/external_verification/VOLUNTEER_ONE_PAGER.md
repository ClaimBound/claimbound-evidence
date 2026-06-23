# Volunteer One-Pager — Close a VERIFY Issue

**You were invited to help close an open verification issue.** This page has
everything you need: what you are checking, exact commands, expected output and
how to post your closing comment.

**Repo:** https://github.com/ClaimBound/claimbound-evidence  
**Release:** use current `main` (see `git rev-parse HEAD` in your report)

## What You Are Doing (30 seconds)

ClaimBound publishes narrow evidence cards for public AI and data claims. The
maintainer already ran the checks. We need **independent GitHub users** (not the
maintainer `NeoZorK`) to confirm the published commands reproduce on **your**
machine.

You are **not** certifying models, approving deployments or endorsing the
project. You only confirm: *these checklist commands work outside the
maintainer's laptop.*

## What You Are NOT Doing

- No model-safety or deployment-readiness claims
- No raw payload commits to the repository
- No PR required (an honest issue comment is enough)
- Maintainer bootstrap runs do **not** count — we need **your** GitHub handle

## Time Budget

| Situation | Realistic time |
| --- | --- |
| First visit (clone + install + baseline) | **15–25 min** |
| One VERIFY pack after setup | **2–10 min** |
| `verify` command alone (after setup) | **~1–2 min** |

Five minutes is enough **only if the repo is already cloned and dependencies
installed.**

## Prerequisites

| Tool | Required | Install hint |
| --- | --- | --- |
| Python 3.12+ | Yes | https://www.python.org/downloads/ |
| git | Yes | https://git-scm.com/downloads |
| uv | Recommended | `pip install uv` or https://docs.astral.sh/uv/ |

Works on **Windows, macOS and Linux**. No bash, jq or curl required for primary
commands. See [platform support](../PLATFORM_SUPPORT.md).

## Step 1 — Baseline (every operator, every machine)

Copy and run exactly:

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
git pull origin main

uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

**Stop if any command fails.** Fix your environment before continuing.

| Command | Expected |
| --- | --- |
| `claimbound doctor` | `ready=yes` |
| `claimbound validate-all` | exit `0`, `valid_cards=33` |
| `pytest -q` | **86 passed** |

Record for your closing comment:

```bash
git rev-parse HEAD
uv run claimbound doctor   # prints today=YYYY-MM-DD
```

## Step 2 — Pick One VERIFY Pack

| Issue | What you confirm | Command (replace `YOUR_HANDLE`) | Time after setup |
| --- | --- | --- | --- |
| [#85](https://github.com/ClaimBound/claimbound-evidence/issues/85) | Starter demos + honest card status fields | `uv run claimbound verify starter-pack` | ~2 min |
| [#86](https://github.com/ClaimBound/claimbound-evidence/issues/86) | NASA POWER positive gate reruns | `uv run claimbound verify nasa-rerun --operator "YOUR_HANDLE"` | ~1–2 min |
| [#87](https://github.com/ClaimBound/claimbound-evidence/issues/87) | NOAA CO-OPS gate stays negative | `uv run claimbound verify noaa-rerun --operator "YOUR_HANDLE"` | ~1–2 min |

**Recommended first task:** #85 (no large downloads, fastest).

**Minimum credible external signal for the project:** close **#85** plus **one
of #86 or #87** from non-maintainer operators. Any single issue you close still
helps.

### #85 — Starter pack

```bash
uv run claimbound verify starter-pack
```

Expected last line:

```text
verify_starter-pack=PASS
```

Confirms: NASA source-byte drift is recorded in `reproduction_level`, not
mislabeled as a failed gate in `result_status`.

### #86 — NASA rerun (needs network)

```bash
uv run claimbound verify nasa-rerun --operator "YOUR_HANDLE"
```

Expected last line:

```text
verify_nasa-rerun=PASS
```

Gate should show `overall_go_no_go: true` and
`result_status: PASSED_UNDER_PROTOCOL`. Different source-byte SHA on rerun is
**honest drift**, not a failure.

### #87 — NOAA rerun (needs network)

```bash
uv run claimbound verify noaa-rerun --operator "YOUR_HANDLE"
```

Expected last line:

```text
verify_noaa-rerun=PASS
```

Gate should show `overall_go_no_go: false` and
`result_status: NEGATIVE_RESULT_UNDER_PROTOCOL`. Do **not** rename a negative
gate as success.

## Step 3 — Post Your Closing Comment

Open the issue you completed (#85, #86 or #87). Paste this block, fill every
field and delete lines that do not apply:

```markdown
## External verification report

- Operator: YOUR_GITHUB_HANDLE
- Date: YYYY-MM-DD
- Repo commit: `FULL_SHA_FROM_git_rev-parse_HEAD`
- Pack: Tier A (#85) | Tier C NASA (#86) | Tier C NOAA (#87)
- Environment: e.g. macOS 15 + Python 3.12.4

### Baseline
- [x] `uv run claimbound validate-all` -> exit 0, `valid_cards=33`
- [x] `uv run --extra dev python -m pytest -q` → 86 passed

### Pack-specific checks
- [x] `uv run claimbound verify starter-pack` → `verify_starter-pack=PASS`
  (paste last 5 lines of terminal output)

### Outcome
- Result: match
- Source-byte drift observed: yes | no | n/a
- Claim boundary OK: yes | n/a

### Limitations
- Single-operator verification only.
- No raw payloads committed to the repository.
- No certification, deployment readiness or model-safety claims.

### Recommendation
Close this VERIFY issue as completed under the narrow checklist above.
```

Full template with all pack lines:
[CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md)

## Step 4 — Close the Issue

- If GitHub lets you close the issue → close it after posting your comment.
- If not → post the comment and ask the maintainer to close after review.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `uv: command not found` | `pip install uv` or use `pip install -e ".[dev]"` from repo root |
| `ready=no` from doctor | Install Python 3.12+, ensure `git` is on PATH |
| `validate-all` fails | `git pull origin main` — you may be on an old commit |
| NASA/NOAA verify times out | Retry; needs outbound HTTPS to NASA POWER / NOAA CO-OPS APIs |
| `verify_*=FAIL` | Paste full terminal output in the issue comment; do not close |
| Not sure about drift vs failure | Read [Common misreadings](../COMMON_MISREADINGS.md) — yellow reproduction chip ≠ red gate |

## Read More (optional)

- [External verification README](README.md) — full pack index
- [Tier A detail](TIER_A_REVIEWER.md) · [NASA](TIER_C_NASA_RERUN.md) · [NOAA](TIER_C_NOAA_RERUN.md)
- [Start without coding](../START_WITHOUT_CODING.md) — non-developer walkthrough

Questions? Comment on the VERIFY issue you are working on or open a
[Discussion](https://github.com/ClaimBound/claimbound-evidence/discussions).
