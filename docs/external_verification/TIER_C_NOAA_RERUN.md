# Tier C — NOAA CO-OPS Rerun Pack

**VERIFY issue:** #87  
**Why:** an independent operator reruns the frozen NOAA CO-OPS D-131 gate and
confirms it stays **negative** under protocol (do not rename failure as success).

**Profile:** fetch NOAA payloads and rerun the frozen negative gate.

Run [baseline](README.md#before-anyone-starts) first. After setup, the primary
command usually finishes in **under 2 minutes** (network dependent).

Playbook: [ISSUE_56_NOAA_RERUN_PLAYBOOK.md](../runbooks/ISSUE_56_NOAA_RERUN_PLAYBOOK.md)

Primary path (any OS):

```bash
uv run claimbound rerun noaa-d131 --operator "<your-handle>"
# or checklist shortcut:
uv run claimbound verify noaa-rerun --operator "<your-handle>"
```

The command fetches frozen D-131 payloads, hashes them, runs the gate and prints
baseline vs your summary.

Expected: `overall_go_no_go: false`, `result_status: NEGATIVE_RESULT_UNDER_PROTOCOL`.  
Do not rename a negative gate as success.

Maintainer rerun card already exists:
`docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-RERUN-2026-06-15.json`.

<details>
<summary>Optional shell (curl + shasum)</summary>

See the legacy bash steps in [ISSUE_56_NOAA_RERUN_PLAYBOOK.md](../runbooks/ISSUE_56_NOAA_RERUN_PLAYBOOK.md).

</details>

Post [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on #87.