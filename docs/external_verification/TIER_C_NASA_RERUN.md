# Tier C — NASA POWER Rerun Pack

**VERIFY issue:** #86  
**Profile:** download three NASA POWER JSON files and rerun the frozen gate.

Run [baseline](README.md#before-anyone-starts) first.

Playbook: [ISSUE_55_NASA_RERUN_PLAYBOOK.md](../runbooks/ISSUE_55_NASA_RERUN_PLAYBOOK.md)

```bash
cd "$REPO_ROOT"

export RUN_DIR="$(
  uv run claimbound run-root \
    --protocol-id "NASA_POWER_D103" \
    --source-url "https://power.larc.nasa.gov/docs/services/api/temporal/daily/" \
    --operator "$OPERATOR" \
    --root "$HOME/claimbound_runs" | head -1
)"
export NASA_RAW="$RUN_DIR/raw"
export NASA_REPORTS="$RUN_DIR/reports"
mkdir -p "$NASA_RAW" "$NASA_REPORTS"
echo "RUN_DIR=$RUN_DIR"

API="https://power.larc.nasa.gov/api/temporal/daily/point"
download_point() {
  local point="$1" lat="$2" lon="$3"
  curl -fsSL \
    "${API}?parameters=ALLSKY_SFC_SW_DWN,T2M,WS10M,PRECTOTCORR&community=RE&longitude=${lon}&latitude=${lat}&start=20150101&end=20241231&format=JSON" \
    -o "$NASA_RAW/${point}.json"
}
download_point POWER_A 50.4501 30.5234
download_point POWER_B 49.8397 24.0297
download_point POWER_C 46.4825 30.7233
shasum -a 256 "$NASA_RAW"/*.json | tee "$RUN_DIR/hashes/nasa_raw_sha256.txt"

uv run python scripts/claimbound_run_nasa_power_prereg.py \
  --point POWER_A --json "$NASA_RAW/POWER_A.json" \
  --point POWER_B --json "$NASA_RAW/POWER_B.json" \
  --point POWER_C --json "$NASA_RAW/POWER_C.json" \
  --report "$NASA_REPORTS/nasa_power_d103_report.json"

echo "=== BASELINE ==="
jq '.result' artifacts/nasa_power_d103_real_run_summary.json
echo "=== YOUR RUN ==="
jq '.result' "$NASA_REPORTS/nasa_power_d103_report.json"
```

Expected gate: `overall_go_no_go: true`, `result_status: PASSED_UNDER_PROTOCOL`.  
Fresh raw SHA-256 usually differs → honest `reproduction_level` drift, not a failed gate.

Maintainer rerun card already exists:
`docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-RERUN-2026-06-15.json`.  
A PR is optional for VERIFY closure; an honest issue comment is enough.

Post [CLOSING_COMMENT_TEMPLATE.md](CLOSING_COMMENT_TEMPLATE.md) on #86.