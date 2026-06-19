# Issue #55 Playbook — NASA POWER D-103 gate-level rerun

Goal: rerun the frozen NASA POWER D-103 gate and publish a `reproduction_attempt`
card if you complete the full PR path.

This is **NASA**, not NOAA. NOAA is issue #56.

## Read first

- `docs/protocols/NASA_POWER_D103_PREREG_CHARTER.md`
- `docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json`
- `artifacts/nasa_power_d103_real_run_summary.json`
- `docs/INDEPENDENT_RERUN_WORKFLOW.md`

## 1. Create local run root

`claimbound run-root` prints the real directory as its **first line** (timestamped name).

```bash
cd "$REPO_ROOT"

export RUN_DIR="$(
  uv run claimbound run-root \
    --protocol-id "NASA_POWER_D103" \
    --source-url "https://power.larc.nasa.gov/docs/services/api/temporal/daily/" \
    --operator "$OPERATOR" \
    --root "$RUNS_ROOT" | head -1
)"
export NASA_RAW="$RUN_DIR/raw"
export NASA_REPORTS="$RUN_DIR/reports"
mkdir -p "$NASA_RAW" "$NASA_REPORTS"

echo "RUN_DIR=$RUN_DIR"
```

## 2. Download 3 official JSON payloads

Points are frozen in `src/claimbound_evidence/nasa_power.py`.

```bash
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
```

## 3. Run frozen gate

```bash
uv run python scripts/claimbound_run_nasa_power_prereg.py \
  --point POWER_A --json "$NASA_RAW/POWER_A.json" \
  --point POWER_B --json "$NASA_RAW/POWER_B.json" \
  --point POWER_C --json "$NASA_RAW/POWER_C.json" \
  --report "$NASA_REPORTS/nasa_power_d103_report.json"
```

## 4. Compare with baseline

```bash
echo "=== BASELINE GATE ==="
jq '.result' "$REPO_ROOT/artifacts/nasa_power_d103_real_run_summary.json"

echo "=== YOUR GATE ==="
jq '.result' "$NASA_REPORTS/nasa_power_d103_report.json"

echo "=== BASELINE INPUT SHA + ROWS ==="
jq '.inputs[] | {point, sha256, rows}' "$REPO_ROOT/artifacts/nasa_power_d103_real_run_summary.json"

echo "=== YOUR INPUT SHA + ROWS (from runner report) ==="
jq '.sources[] | {point_id, json_sha256, rows}' "$NASA_REPORTS/nasa_power_d103_report.json" 2>/dev/null \
  || jq '.points[]? | {point, sha256, rows}' "$NASA_REPORTS/nasa_power_d103_report.json"

echo "=== YOUR RAW FILE SHA ==="
cat "$RUN_DIR/hashes/nasa_raw_sha256.txt"
```

Expected gate (baseline):

```text
source_audit_passed: true
eligible_point_count: 3
eligible_windows: 15
overall_go_no_go: true
result_status: PASSED_UNDER_PROTOCOL
```

Interpretation:

| Gate outcome | Raw SHA vs baseline | `reproduction_level` |
| --- | --- | --- |
| same | same | `REPRODUCED_OUTCOME` |
| same | different | `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` |
| different | any | record mismatch honestly |

## 5. Maintainer rerun card (already in registry)

The maintainer `reproduction_attempt` card is already committed:

- `docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-RERUN-2026-06-15.json`
- `artifacts/nasa_power_d103_maintainer_rerun_summary.json`
- registry entry in `docs/registry/evidence_index.json`

External operators should still use this playbook for their own local rerun
evidence. A new PR is optional for VERIFY #86 closure; an honest issue comment
with gate comparison is enough.

## 6. Optional external PR path

If you publish your own rerun card:

```bash
cp "$NASA_REPORTS/nasa_power_d103_report.json" \
   "$REPO_ROOT/artifacts/nasa_power_d103_<operator>_rerun_summary.json"

uv run claimbound validate-all
uv run --extra dev python -m pytest -n auto -q
```

Use `record_type: reproduction_attempt`, set `verification_level` honestly and
open a PR with `.github/PULL_REQUEST_TEMPLATE/reproduction_rerun.md`.
