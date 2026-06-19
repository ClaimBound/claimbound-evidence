# Tier B — EEA Source Drift Pack

**VERIFY issue:** #88  
**Profile:** one public-data network probe.

Run [baseline](README.md#before-anyone-starts) first.

Playbook: [ISSUE_57_EEA_DRIFT_PLAYBOOK.md](../runbooks/ISSUE_57_EEA_DRIFT_PLAYBOOK.md)

```bash
cd "$REPO_ROOT"

jq '{
  http_status,
  final_url,
  page_sha256,
  rights_link_present,
  direct_link_presence,
  result_status
}' artifacts/source_audit_d001_summary.json

uv run python scripts/claimbound_run_eea_source_audit.py \
  --report artifacts/eea_source_audit_drift_check_summary.json

jq '{
  http_status,
  final_url,
  page_sha256,
  rights_link_present,
  direct_link_presence,
  result_status
}' artifacts/eea_source_audit_drift_check_summary.json

diff <(
  jq -S '{http_status,final_url,content_type,page_sha256,page_byte_size,page_title,rights_link_present,direct_link_presence}' \
    artifacts/source_audit_d001_summary.json
) <(
  jq -S '{http_status,final_url,content_type,page_sha256,page_byte_size,page_title,rights_link_present,direct_link_presence}' \
    artifacts/eea_source_audit_drift_check_summary.json
) || true
```

Record in your issue comment:

- whether `page_sha256` changed;
- whether marker fields (`rights_link_present`, `direct_link_presence`) still pass;
- that source drift does not automatically invalidate the original card.

Post [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on #88.