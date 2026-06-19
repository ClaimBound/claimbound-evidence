# Tier C — NASA POWER Rerun Pack

**VERIFY issue:** #86  
**Profile:** download three NASA POWER JSON files and rerun the frozen gate.

Run [baseline](README.md#before-anyone-starts) first.

Playbook: [ISSUE_55_NASA_RERUN_PLAYBOOK.md](../runbooks/ISSUE_55_NASA_RERUN_PLAYBOOK.md)

Primary path (any OS, no curl or shasum):

```bash
uv run claimbound rerun nasa-d103 --operator "<your-handle>"
# or checklist shortcut:
uv run claimbound verify nasa-rerun --operator "<your-handle>"
```

The command creates a local run directory, downloads three frozen JSON payloads,
writes SHA-256 hashes, runs the gate and prints baseline vs your run.

Expected gate: `overall_go_no_go: true`, `result_status: PASSED_UNDER_PROTOCOL`.  
Fresh raw SHA-256 usually differs → honest `reproduction_level` drift, not a failed gate.

Maintainer rerun card already exists:
`docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-RERUN-2026-06-15.json`.  
A PR is optional for VERIFY closure; an honest issue comment is enough.

<details>
<summary>Optional shell (curl + shasum)</summary>

See the legacy bash steps in [ISSUE_55_NASA_RERUN_PLAYBOOK.md](../runbooks/ISSUE_55_NASA_RERUN_PLAYBOOK.md).

</details>

Post [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on #86.