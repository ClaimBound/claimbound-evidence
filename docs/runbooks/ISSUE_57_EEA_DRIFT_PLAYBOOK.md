# Issue #57 Playbook — EEA source drift check

Goal: check whether the EEA download page used by the source-audit card changed
since `2026-05-08`. Source drift is not automatically an invalid card.

## Quick path (any OS)

```bash
uv run claimbound drift eea-source-audit
```

## Read first

- `docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json`
- `artifacts/source_audit_d001_summary.json`
- `docs/protocols/SOURCE_AUDIT_D001_PREREG_CHARTER.md`

## 1. Baseline values

```bash
cd "$REPO_ROOT"

jq '{
  http_status,
  final_url,
  content_type,
  page_sha256,
  page_byte_size,
  page_title,
  rights_link_present,
  direct_link_presence,
  result_status
}' artifacts/source_audit_d001_summary.json
```

Baseline page SHA-256:

```text
beb658db375df6eac841da35484243ff2d0799b0f3d71ba86be6355fb765d51b
```

## 2. Fresh probe

```bash
uv run python scripts/claimbound_run_eea_source_audit.py \
  --report artifacts/eea_source_audit_drift_check_summary.json
```

## 3. Diff

```bash
echo "=== FRESH ==="
jq '{
  http_status,
  final_url,
  content_type,
  page_sha256,
  page_byte_size,
  page_title,
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

## 4. Operator report

```bash
mkdir -p docs/operator_trials

cat > "docs/operator_trials/EEA_SOURCE_DRIFT_CHECK_${TODAY}.md" <<EOF
# EEA source drift check (${TODAY})

Original card: docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json
Baseline: artifacts/source_audit_d001_summary.json
Fresh: artifacts/eea_source_audit_drift_check_summary.json

## Drift observed?
YES / NO

## Changed fields


## Card boundary impact
Source drift only / affects claim — explain:

## Forbidden claim
Do not say the original card is invalid unless protocol evidence supports that.
EOF
```

## 5. PR path

- **No drift:** commit report + `eea_source_audit_drift_check_summary.json`
- **Drift:** same, optionally add `reproduction_attempt` card with
  `reproduction_level: REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` while keeping
  the honest gate outcome in `result_status`

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest tests/test_eea_source_audit.py -n auto -q
```

Closes #57.
