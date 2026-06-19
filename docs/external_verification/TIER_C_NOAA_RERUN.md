# Tier C — NOAA CO-OPS Rerun Pack

**VERIFY issue:** #87  
**Profile:** fetch NOAA payloads and rerun the frozen negative gate.

Run [baseline](README.md#before-anyone-starts) first.

Playbook: [ISSUE_56_NOAA_RERUN_PLAYBOOK.md](../runbooks/ISSUE_56_NOAA_RERUN_PLAYBOOK.md)

```bash
cd "$REPO_ROOT"

export RUN_DIR="$(
  uv run claimbound run-root \
    --protocol-id "NOAA_COOPS_D131" \
    --source-url "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter" \
    --operator "$OPERATOR" \
    --root "$HOME/claimbound_runs" | head -1
)"
export NOAA_RAW="$RUN_DIR/raw"
export NOAA_REPORTS="$RUN_DIR/reports"
mkdir -p "$NOAA_RAW" "$NOAA_REPORTS"
echo "RUN_DIR=$RUN_DIR"
test -n "$RUN_DIR" && test -d "$RUN_DIR"

uv run python scripts/fetch_noaa_coops_d131_payloads.py --out-dir "$NOAA_RAW"
shasum -a 256 "$NOAA_RAW"/*.json | tee "$RUN_DIR/hashes/raw_sha256.txt"

uv run python scripts/claimbound_run_noaa_coops_prereg.py \
  --raw-dir "$NOAA_RAW" \
  --report "$NOAA_REPORTS/noaa_coops_d131_report.json" \
  --summary "$NOAA_REPORTS/noaa_coops_d131_summary.json"

echo "=== BASELINE GATE ==="
jq '.result' artifacts/noaa_coops_d131_negative_result_summary.json
echo "=== YOUR GATE ==="
jq '.result' "$NOAA_REPORTS/noaa_coops_d131_summary.json"
echo "=== YOUR FAILED GATES ==="
jq '.failed_gates' "$NOAA_REPORTS/noaa_coops_d131_summary.json"
```

Expected: `overall_go_no_go: false`, `result_status: NEGATIVE_RESULT_UNDER_PROTOCOL`.  
Do not rename a negative gate as success.

Maintainer rerun card already exists:
`docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-RERUN-2026-06-15.json`.

Post [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on #87.