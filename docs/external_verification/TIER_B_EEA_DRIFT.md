# Tier B — EEA Source Drift Pack

**VERIFY issue:** #88  
**Profile:** one public-data network probe.

Run [baseline](README.md#before-anyone-starts) first.

Playbook: [ISSUE_57_EEA_DRIFT_PLAYBOOK.md](../runbooks/ISSUE_57_EEA_DRIFT_PLAYBOOK.md)

Primary path (any OS, no jq or bash diff):

```bash
uv run claimbound drift eea-source-audit
# or checklist shortcut:
uv run claimbound verify eea-drift
```

Record in your issue comment:

- whether `page_sha256` changed;
- whether marker fields (`rights_link_present`, `direct_link_presence`) still pass;
- that source drift does not automatically invalidate the original card.

<details>
<summary>Optional shell (jq + diff)</summary>

```bash
uv run claimbound inspect json artifacts/source_audit_d001_summary.json \
  --keys http_status final_url page_sha256 rights_link_present direct_link_presence result_status
```

</details>

Post [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on #88.