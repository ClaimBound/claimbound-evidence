# GitHub Outreach — Copy-Paste Messages for Maintainers

Use these templates to invite **random GitHub volunteers** to close open VERIFY
issues [#85](https://github.com/ClaimBound/claimbound-evidence/issues/85),
[#86](https://github.com/ClaimBound/claimbound-evidence/issues/86) or
[#87](https://github.com/ClaimBound/claimbound-evidence/issues/87).

**Send volunteers here:** [VOLUNTEER_ONE_PAGER.md](VOLUNTEER_ONE_PAGER.md)  
(link: `https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/VOLUNTEER_ONE_PAGER.md`)

---

## Template A — One line (tweet, short reply)

```text
ClaimBound needs independent operators to run 3 copy-paste verify commands (~15 min first time). Guide: https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/VOLUNTEER_ONE_PAGER.md — issues #85 #86 #87
```

---

## Template B — Short DM (under 500 characters)

```text
Hi — would you run a narrow reproducibility checklist on ClaimBound (open-source evidence-card toolkit)?

Not a code review: clone repo, run baseline + one `claimbound verify` command, post a short report on GitHub issue #85, #86 or #87.

~15 min first time, ~2 min per check after setup. Full steps:
https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/VOLUNTEER_ONE_PAGER.md

No certification claims, no PR required. Maintainer runs don't count — we need your handle on the closing comment.
```

---

## Template C — Issue comment (pin on #85, #86 or #87)

```markdown
### Looking for independent operators

We need **non-maintainer** GitHub users to confirm the published checklist
reproduces outside the maintainer machine.

**Start here (one page, all commands):**
https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/VOLUNTEER_ONE_PAGER.md

| Issue | Task | Time after setup |
| --- | --- | --- |
| #85 | `uv run claimbound verify starter-pack` | ~2 min |
| #86 | `uv run claimbound verify nasa-rerun --operator "<your-handle>"` | ~1–2 min |
| #87 | `uv run claimbound verify noaa-rerun --operator "<your-handle>"` | ~1–2 min |

**First visit:** budget 15–25 min (clone + `uv sync` + baseline).

Post your report using [CLOSING_COMMENT_TEMPLATE.md](https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/CLOSING_COMMENT_TEMPLATE.md) and close the issue (or ask us to close).

You are **not** certifying models or approving deployments — only confirming commands work on your machine.
```

---

## Template D — Discussions post (repo Discussions → General)

**Title:** `Volunteers wanted: run one VERIFY checklist (~15 min)`

```markdown
ClaimBound publishes narrow evidence cards for public AI and data claims. Three VERIFY issues are open for **independent** closure — we need operators who are **not** the maintainer (`NeoZorK`).

### What you do
1. Clone the repo and run a 4-command baseline (~15 min first time)
2. Run **one** `claimbound verify` command for #85, #86 or #87 (~2 min)
3. Paste a short report on the issue and close it

### Full guide (copy-paste commands)
https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/VOLUNTEER_ONE_PAGER.md

### Open issues
- #85 — starter pack (easiest, start here)
- #86 — NASA POWER gate rerun (needs network)
- #87 — NOAA CO-OPS negative gate rerun (needs network)

### What this is NOT
- Not a model-safety certification
- Not a deployment approval
- Not a PR or long code review

Comment on the issue you picked when done (or if you get stuck). Thanks!
```

---

## Template E — Reply when someone says yes

```markdown
Thanks! Pick **one** issue to start (recommend #85):

**Guide:** https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/external_verification/VOLUNTEER_ONE_PAGER.md

Quick path:
```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
uv run claimbound verify starter-pack   # for #85
```

Post your closing comment on the issue using the template in the guide. Paste `verify_*=PASS` and your `git rev-parse HEAD`.

If anything fails, paste the full terminal output on the issue — don't close yet.
```

---

## Template F — Example filled closing comment (show volunteers)

```markdown
## External verification report

- Operator: jane-reviewer
- Date: 2026-06-19
- Repo commit: `5cd37c0abc123...` (full SHA)
- Pack: Tier A (#85)
- Environment: Ubuntu 24.04 + Python 3.12.3

### Baseline
- [x] `uv run claimbound validate-all` -> exit 0, `valid_cards=33`
- [x] `uv run --extra dev python -m pytest -q` → 86 passed

### Pack-specific checks
- [x] `uv run claimbound verify starter-pack` → `verify_starter-pack=PASS`

```
verify_starter-pack: demo_eea=PASS demo_grok=PASS card_nasa_reproduction_level=PASS
verify_starter-pack=PASS
```

### Outcome
- Result: match
- Source-byte drift observed: n/a
- Claim boundary OK: yes

### Limitations
- Single-operator verification only.
- No raw payloads committed to the repository.
- No certification, deployment readiness or model-safety claims.

### Recommendation
Close this VERIFY issue as completed under the narrow checklist above.
```

---

## Where to find volunteers

| Channel | How |
| --- | --- |
| VERIFY issues | Post Template C on #85, #86, #87 |
| Repo Discussions | Post Template D |
| Good-first-issue hunters | Link VOLUNTEER_ONE_PAGER in replies to "looking for OSS tasks" threads |
| Direct DM | Template B to people who already engage with reproducibility / open-data repos |

## Maintainer checklist after a volunteer posts

1. Confirm operator is **not** `NeoZorK` / maintainer bot
2. Confirm `verify_*=PASS` or honest mismatch report with logs
3. Confirm commit SHA is recent `main`
4. Close issue if volunteer could not
5. For credibility: aim for **#85 + one of #86/#87** from different handles

See [MAINTAINER_TRIAGE.md](MAINTAINER_TRIAGE.md) for review rules.
