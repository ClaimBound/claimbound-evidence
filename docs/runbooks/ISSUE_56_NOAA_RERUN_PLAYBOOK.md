# Issue #56 Playbook — NOAA CO-OPS D-131 negative rerun

Goal: rerun the frozen NOAA D-131 protocol and record the same **negative** gate
honestly. Do not turn a negative result into success.

## Important limits in this repository

| Step | Status |
| --- | --- |
| Download official payloads | **Supported** — `scripts/fetch_noaa_coops_d131_payloads.py` |
| Statistical gate evaluator | **Supported** — `scripts/claimbound_run_noaa_coops_prereg.py` |
| Full reproduction card PR | Ready once rerun artifacts are committed |

## Common mistakes

1. **Wrong issue** — `jq '.inputs' artifacts/noaa_coops_d131_negative_result_summary.json` is **NOAA #56**, not NASA #55.
2. **`mapfile` in zsh** — macOS default shell is zsh; use `RUN_DIR="$(uv run claimbound run-root ... | head -1)"` instead of bash `mapfile`.
3. **Wrong path** — if `RUN_DIR` is empty, `NOAA_RAW` becomes `/raw` and fetch fails. Always `echo "$RUN_DIR"` before fetch.
4. **Wrong curl range** — one 2018–2024 request returns HTTP 400 (`365 days` NOAA limit). Use the fetch script.
5. **Wrong SHA expectation** — fresh merged JSON will usually **not** match committed baseline SHA-256. Compare **`joined_rows` first**, then gate outcome once runner exists.

## Read first

- `docs/protocols/NOAA_COOPS_D131_PREREG_CHARTER.md`
- `docs/evidence/NOAA_COOPS_D131_NEGATIVE_RESULT.md`
- `artifacts/noaa_coops_d131_negative_result_summary.json`
- `docs/REPRODUCTION.md` (NOAA CO-OPS D-131 section)

## 1. Create local run root

```bash
cd "$REPO_ROOT"

export RUN_DIR="$(
  uv run claimbound run-root \
    --protocol-id "NOAA_COOPS_D131" \
    --source-url "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter" \
    --operator "$OPERATOR" \
    --root "$RUNS_ROOT" | head -1
)"
export NOAA_RAW="$RUN_DIR/raw"
export NOAA_HASHES="$RUN_DIR/hashes"
export NOAA_REPORTS="$RUN_DIR/reports"
mkdir -p "$NOAA_RAW" "$NOAA_HASHES" "$NOAA_REPORTS"

echo "RUN_DIR=$RUN_DIR"
test -n "$RUN_DIR" && test -d "$RUN_DIR" || { echo "RUN_DIR missing; stop." >&2; exit 1; }
```

## 2. Download merged payloads (yearly API chunks)

```bash
uv run python scripts/fetch_noaa_coops_d131_payloads.py \
  --out-dir "$NOAA_RAW"

shasum -a 256 "$NOAA_RAW"/*.json | tee "$NOAA_HASHES/raw_sha256.txt"
```

This creates 6 files:

```text
8518750_observed.json
8518750_predictions.json
9414290_observed.json
9414290_predictions.json
8638610_observed.json
8638610_predictions.json
```

## 3. Compare with baseline (rows, not only SHA)

```bash
echo "=== BASELINE (committed summary) ==="
jq '.inputs' "$REPO_ROOT/artifacts/noaa_coops_d131_negative_result_summary.json"

echo "=== YOUR ROW COUNTS + SHA PREFIX ==="
uv run python - <<PY
import hashlib
import json
from pathlib import Path

raw = Path("$NOAA_RAW")
baseline = json.loads(
    Path("$REPO_ROOT/artifacts/noaa_coops_d131_negative_result_summary.json").read_text()
)

def count_rows(path: Path) -> int:
    data = json.loads(path.read_text())
    if "data" in data:
        return len(data["data"])
    return len(data["predictions"])

for item in baseline["inputs"]:
    station = item["station"]
    obs = raw / f"{station}_observed.json"
    pred = raw / f"{station}_predictions.json"
    obs_rows = count_rows(obs)
    pred_rows = count_rows(pred)
    joined = min(obs_rows, pred_rows)
    obs_sha = hashlib.sha256(obs.read_bytes()).hexdigest()
    print(f"station {station}")
    print(f"  baseline joined_rows={item['joined_rows']}")
    print(f"  your obs_rows={obs_rows} pred_rows={pred_rows} joined={joined}")
    print(f"  baseline observed_sha256={item['observed_sha256'][:16]}...")
    print(f"  your observed_sha256={obs_sha[:16]}...")
PY

echo "=== YOUR SHA FILE ==="
cat "$NOAA_HASHES/raw_sha256.txt"
```

Expected baseline rows:

| Station | joined_rows |
| --- | ---: |
| 8518750 | 61368 |
| 9414290 | 56424 |
| 8638610 | 61368 |

If `joined_rows` match but SHA differ: **source-byte drift** (normal).

Expected gate once runner exists:

```text
source_audit_passed: true
eligible_station_count: 3
eligible_windows: 11
overall_go_no_go: false
result_status: NEGATIVE_RESULT_UNDER_PROTOCOL
```

Failed gates (must stay failed unless protocol changes):

- seasonal hour-of-year residual control was not beaten
- event rate below minimum in one window
- event rate above maximum in one window

## 4. Run frozen gate

```bash
uv run python scripts/claimbound_run_noaa_coops_prereg.py \
  --raw-dir "$NOAA_RAW" \
  --report "$NOAA_REPORTS/noaa_coops_d131_report.json" \
  --summary "$NOAA_REPORTS/noaa_coops_d131_summary.json"

echo "=== BASELINE GATE ==="
jq '.result' "$REPO_ROOT/artifacts/noaa_coops_d131_negative_result_summary.json"

echo "=== YOUR GATE ==="
jq '.result' "$NOAA_REPORTS/noaa_coops_d131_summary.json"

echo "=== YOUR FAILED GATES ==="
jq '.failed_gates' "$NOAA_REPORTS/noaa_coops_d131_summary.json"
```

## 5. What you can close now vs later

**Now (operator evidence short of full card):**

- payloads downloaded outside repo
- `RUN_DIR/hashes/raw_sha256.txt` recorded
- row-count comparison documented in `docs/operator_trials/NOAA_D131_RERUN_${TODAY}.md`

**Later (full #56 PR):**

- copy summary to `artifacts/noaa_coops_d131_maintainer_rerun_summary.json`
- `reproduction_attempt` card + registry + PR template

## 6. Optional operator note

```bash
mkdir -p "$REPO_ROOT/docs/operator_trials"
cat > "$REPO_ROOT/docs/operator_trials/NOAA_D131_RERUN_${TODAY}.md" <<EOF
# NOAA D-131 operator rerun note (${TODAY})

RUN_DIR: ${RUN_DIR}
Operator: ${OPERATOR}

Row-count check: PASS/FAIL
SHA match baseline: expected NO for fresh official payloads
Gate runner: not available in repository yet
EOF
```
