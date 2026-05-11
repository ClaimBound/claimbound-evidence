# EEA AQ D-001 Manual Track Checklist

This is a command-driven manual checklist for the EEA Air Quality D-001 track. It is a runbook, not a completed result.

The track audits **source readiness and PM10 daily coverage only**. It does **not** claim forecasting performance, deployment readiness, model superiority, health impact, or production suitability.

General manual audit rules are defined in [`docs/MANUAL_AUDIT_PROTOCOL.md`](../MANUAL_AUDIT_PROTOCOL.md).

---

## 0. Operator Promise

```text
I fixed source, selection, target, controls, coverage rule and acceptance gate before scoring.
I did not remove weak data after seeing outcomes.
I did not tune thresholds after seeing outcomes.
I did not rewrite a negative or blocked outcome as a positive claim.
I recorded deviations and limitations.
```

- [ ] I accept the operator promise.
- [ ] I understand that pass, insufficient coverage, blocked source, and negative result are all valid honest outcomes.
- [ ] I will keep raw payloads outside this repository.

---

## 1. Fixed Scope

Do not change this after starting the run.

```text
Track ID: EEA_AQ_D001
Claim type: source audit
Official source: EEA Air Quality Download Service
Dataset: verified E1a data
Pollutant: PM10
Countries: NL, BE, DE
Period: 2018-01-01 through 2024-12-31
Aggregation: daily records
Coverage gate: at least 85 percent daily coverage per sampling point
Selection rule: first five eligible sampling points per country after sorting by country code, city/locality if available, and sampling point ID
Raw payload policy: raw files stay outside this repository
Public output policy: commit only sanitized summary, evidence card JSON, evidence card SVG, and registry update
```

Allowed final statuses:

- `PASSED_UNDER_PROTOCOL`
- `INSUFFICIENT_COVERAGE`
- `BLOCKED_SOURCE`
- `NEGATIVE_RESULT_UNDER_PROTOCOL`

Status decision rules:

- `PASSED_UNDER_PROTOCOL`: source is accessible, rights are acceptable for sanitized public evidence, and all three countries have at least five eligible PM10 daily sampling points.
- `INSUFFICIENT_COVERAGE`: data is accessible and parseable, but at least one country has fewer than five eligible sampling points.
- `BLOCKED_SOURCE`: access, rights, documentation, download, metadata, timestamps, units, or file format prevents a fair run.
- `NEGATIVE_RESULT_UNDER_PROTOCOL`: valid non-coverage negative result under this fixed source-audit protocol.

- [ ] Fixed scope reviewed.
- [ ] Status rules reviewed.
- [ ] No source data inspected yet.

---

## 2. Exact Files Used By This Run

Local-only files outside the repository:

```text
$RUN_ROOT/logs/operator_log.md
$RUN_ROOT/logs/run_env.sh
$RUN_ROOT/logs/protocol_lock.txt
$RUN_ROOT/hashes/protocol_lock.sha256
$RUN_ROOT/hashes/raw_payloads.sha256
$RUN_ROOT/hashes/raw_payloads_manifest.sha256
$RUN_ROOT/reports/station_coverage.csv
$RUN_ROOT/reports/selected_sampling_points.csv
$RUN_ROOT/reports/eea_aq_d001_manual_summary.json
```

Only this file may be copied into the repository after review:

```text
$RUN_ROOT/reports/eea_aq_d001_manual_summary.json
```

- [ ] I know which files are local-only.
- [ ] I know which summary file may become public after review.

---

## 3. Start Run And Freeze Protocol

Run from the public repository root.

```bash
set -euo pipefail

CLAIMBOUND_REPO="$(pwd -P)"
git status --short --branch

STARTING_GIT_COMMIT="$(git rev-parse --short HEAD)"
RUN_STARTED_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
RUN_ID="eea_aq_d001_$(date -u +%Y%m%d_%H%M%S)"
RUN_ROOT="$HOME/claimbound_runs/$RUN_ID"
OPERATOR_NAME="YOUR_PUBLIC_OPERATOR_NAME"
EXECUTION_MODE="MANUAL_NO_AI"

mkdir -p "$RUN_ROOT"/{raw,downloads,hashes,logs,reports,scripts,work}

cat > "$RUN_ROOT/logs/run_env.sh" <<EOF
export CLAIMBOUND_REPO="$CLAIMBOUND_REPO"
export RUN_ID="$RUN_ID"
export RUN_ROOT="$RUN_ROOT"
export STARTING_GIT_COMMIT="$STARTING_GIT_COMMIT"
export RUN_STARTED_UTC="$RUN_STARTED_UTC"
export OPERATOR_NAME="$OPERATOR_NAME"
export EXECUTION_MODE="$EXECUTION_MODE"
EOF

cat > "$RUN_ROOT/logs/protocol_lock.txt" <<EOF
Track ID: EEA_AQ_D001
Claim type: source audit
Official source: EEA Air Quality Download Service
Dataset: verified E1a data
Pollutant: PM10
Countries: NL, BE, DE
Period: 2018-01-01 through 2024-12-31
Aggregation: daily records
Coverage gate: at least 85 percent daily coverage per sampling point
Selection rule: first five eligible sampling points per country after sorting by country code, city/locality if available, and sampling point ID
Raw payload policy: raw files stay outside this repository
Public output policy: commit only sanitized summary, evidence card JSON, evidence card SVG, and registry update
Execution mode: $EXECUTION_MODE
EOF

shasum -a 256 "$RUN_ROOT/logs/protocol_lock.txt" > "$RUN_ROOT/hashes/protocol_lock.sha256"

cat > "$RUN_ROOT/logs/operator_log.md" <<EOF
# EEA AQ D-001 Operator Log

## Run Identity
Track ID: EEA_AQ_D001
Operator: $OPERATOR_NAME
Execution mode: $EXECUTION_MODE
Run started UTC: $RUN_STARTED_UTC
Starting git commit: $STARTING_GIT_COMMIT
Public repository: $CLAIMBOUND_REPO
External run root: $RUN_ROOT

## Protocol Lock
Protocol lock file: $RUN_ROOT/logs/protocol_lock.txt
Protocol lock SHA-256: $(awk '{print $1}' "$RUN_ROOT/hashes/protocol_lock.sha256")

## Source Rights Decision
Sanitized public summaries allowed: NOT_RECORDED_YET
Raw payload files committed: no

## Download Notes
Download method: NOT_RECORDED_YET
Summary count: NOT_RECORDED_YET
Summary size: NOT_RECORDED_YET
Downloaded files: NOT_RECORDED_YET

## Processing Notes
Runtime versions: NOT_RECORDED_YET
Raw payload manifest SHA-256: NOT_RECORDED_YET
Sanitized summary SHA-256: NOT_RECORDED_YET

## Status Decision
Result status: NOT_RECORDED_YET
Reason: NOT_RECORDED_YET
Deviations: none recorded yet
Known limitations: source-readiness and coverage audit only; no forecasting claim
EOF

printf 'Run root: %s\n' "$RUN_ROOT"
printf 'Reload later with: source "%s/logs/run_env.sh"\n' "$RUN_ROOT"
```

Check:

```bash
source "$RUN_ROOT/logs/run_env.sh"
cat "$RUN_ROOT/hashes/protocol_lock.sha256"
test -f "$RUN_ROOT/logs/operator_log.md" && echo OK
```

- [ ] Repository status checked before run.
- [ ] `$RUN_ROOT` created outside repository.
- [ ] `operator_log.md` created.
- [ ] `protocol_lock.txt` created.
- [ ] `protocol_lock.sha256` created before data inspection.

---

## 4. Source And Rights Check

Open these official pages manually:

```text
https://aqportal.discomap.eea.europa.eu/download-data/
https://eeadmz1-downloads-webapp.azurewebsites.net/
https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html
https://eeadmz1-downloads-webapp.azurewebsites.net/content/documentation/How_To_Downloads.pdf
https://www.eea.europa.eu/en/legal-notice
https://www.eea.europa.eu/en/about/contact-us/faqs/can-i-use-eea-content-in-my-work-or-in-my-organisations-products
```

Record the decision. If rights are unclear, use `BLOCKED_SOURCE`.

```bash
source "$RUN_ROOT/logs/run_env.sh"
SOURCE_RIGHTS_DECISION="REPLACE_WITH_ALLOWED_OR_BLOCKED_AND_REASON"

cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## Official Source Links Checked
Download page: https://aqportal.discomap.eea.europa.eu/download-data/
Web application: https://eeadmz1-downloads-webapp.azurewebsites.net/
API Swagger: https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html
Documentation PDF: https://eeadmz1-downloads-webapp.azurewebsites.net/content/documentation/How_To_Downloads.pdf
Legal notice: https://www.eea.europa.eu/en/legal-notice
Reuse FAQ: https://www.eea.europa.eu/en/about/contact-us/faqs/can-i-use-eea-content-in-my-work-or-in-my-organisations-products

## Source Rights Decision Recorded
Sanitized public summaries allowed: $SOURCE_RIGHTS_DECISION
Raw payload files committed: no
Raw payload folder: $RUN_ROOT/raw
EOF
```

- [ ] Download page opened.
- [ ] Web application opened.
- [ ] API Swagger opened.
- [ ] Documentation PDF opened or attempted.
- [ ] Legal/reuse pages opened.
- [ ] Rights decision recorded.
- [ ] If rights were unclear, I stopped and used `BLOCKED_SOURCE`.

---

## 5. Download Data

Use the web application first. Use Swagger only if the web application fails.

Fixed filters:

```text
Countries: NL, BE, DE
Pollutant: PM10
Dataset: verified E1a data
Aggregation/type: daily records
Start: 2018-01-01 or 2018-01-01T00:00:00Z
End: 2024-12-31 or 2024-12-31T23:59:59Z
City/locality: blank
Email: blank unless you choose to provide one
```

Record web summary if available:

```bash
source "$RUN_ROOT/logs/run_env.sh"
WEBAPP_SUMMARY_COUNT="REPLACE_WITH_UI_COUNT_OR_NOT_AVAILABLE"
WEBAPP_SUMMARY_SIZE="REPLACE_WITH_UI_SIZE_OR_NOT_AVAILABLE"

cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## Web Application Summary
Summary count: $WEBAPP_SUMMARY_COUNT
Summary size: $WEBAPP_SUMMARY_SIZE
EOF
```

Move downloaded files outside the repository. Edit filenames before running:

```bash
mv "$HOME/Downloads/REPLACE_WITH_FILE.zip" "$RUN_ROOT/raw/"
# or
mv "$HOME/Downloads/REPLACE_WITH_FILE.parquet" "$RUN_ROOT/raw/"
# or, if the UI gives URL lists:
mv "$HOME/Downloads/REPLACE_WITH_URL_LIST.csv" "$RUN_ROOT/downloads/"
```

If using Swagger fallback, record the request:

```bash
API_REQUEST_USED="REPLACE_WITH_SWAGGER_REQUEST_URL_OR_BODY_OR_NOT_USED"
API_HTTP_STATUS="REPLACE_WITH_HTTP_STATUS_OR_NOT_USED"

cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## API Fallback
API request used: $API_REQUEST_USED
API HTTP status: $API_HTTP_STATUS
EOF
```

If Swagger gives parquet URLs, paste them into `$RUN_ROOT/downloads/parquet_urls.txt`, then run:

```bash
touch "$RUN_ROOT/downloads/parquet_urls.txt"
${EDITOR:-nano} "$RUN_ROOT/downloads/parquet_urls.txt"

cd "$RUN_ROOT/raw"
while IFS= read -r url; do
  [ -z "$url" ] && continue
  filename="$(basename "${url%%\?*}")"
  curl -L --fail --retry 3 --output "$filename" "$url"
done < "$RUN_ROOT/downloads/parquet_urls.txt"
```

Record files:

```bash
cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## Downloaded Files Stored Outside Repository
Raw folder: $RUN_ROOT/raw
$(find "$RUN_ROOT/raw" -maxdepth 1 -type f -print | sort)

Download helper folder: $RUN_ROOT/downloads
$(find "$RUN_ROOT/downloads" -maxdepth 1 -type f -print | sort)
EOF
```

- [ ] Fixed filters used exactly.
- [ ] Web application used, or Swagger fallback reason recorded.
- [ ] Raw data moved to `$RUN_ROOT/raw`.
- [ ] Helper URL files moved to `$RUN_ROOT/downloads`.
- [ ] Downloaded files recorded.
- [ ] If download failed, I stopped and used `BLOCKED_SOURCE`.

---

## 6. Freeze Raw Payloads

```bash
source "$RUN_ROOT/logs/run_env.sh"
cd "$RUN_ROOT"

find raw -type f | sort

mkdir -p work/extracted
find raw -name '*.zip' -print0 | while IFS= read -r -d '' z; do
  unzip -n "$z" -d work/extracted
done

find raw work/extracted -type f | sort | xargs shasum -a 256 > hashes/raw_payloads.sha256
shasum -a 256 hashes/raw_payloads.sha256 > hashes/raw_payloads_manifest.sha256

cat >> logs/operator_log.md <<EOF

## Raw Payload Hashes
Raw payload manifest SHA-256: $(awk '{print $1}' hashes/raw_payloads_manifest.sha256)
Raw payload files committed: no
EOF
```

- [ ] Raw files listed.
- [ ] ZIP files extracted to `$RUN_ROOT/work/extracted`, if present.
- [ ] `raw_payloads.sha256` created.
- [ ] `raw_payloads_manifest.sha256` created.
- [ ] Manifest hash recorded.
- [ ] No raw payload copied into the repository.

---

## 7. Create Local Processing Environment

```bash
source "$RUN_ROOT/logs/run_env.sh"
cd "$RUN_ROOT"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas pyarrow

python - <<'PY' | tee "$RUN_ROOT/work/runtime_versions.txt"
import pandas as pd
import pyarrow as pa
import sys
print("python", sys.version.replace("\n", " "))
print("pandas", pd.__version__)
print("pyarrow", pa.__version__)
PY

cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## Runtime Versions
$(cat "$RUN_ROOT/work/runtime_versions.txt")
EOF
```

- [ ] Virtual environment created outside repository.
- [ ] `pandas` and `pyarrow` installed.
- [ ] Runtime versions recorded.

---

## 8. Create Inspection Script

This helper script runs after the protocol is frozen. Do not tune thresholds, dates, countries, or station-selection rules after seeing output.

```bash
source "$RUN_ROOT/logs/run_env.sh"
cat > "$RUN_ROOT/scripts/inspect_eea_aq_d001.py" <<'PY'
from __future__ import annotations
import json, re
from pathlib import Path
import pandas as pd

RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)
START = pd.Timestamp("2018-01-01")
END = pd.Timestamp("2024-12-31")
EXPECTED_DAYS = (END - START).days + 1
MIN_COVERAGE = 0.85
COUNTRIES = {"NL", "BE", "DE"}
INPUT_DIRS = [RUN_ROOT / "raw", RUN_ROOT / "work" / "extracted"]

def norm(x): return str(x).strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def find_col(cols, names):
    lookup = {norm(c): c for c in cols}
    for n in names:
        if norm(n) in lookup: return lookup[norm(n)]
    for c in cols:
        if any(norm(n) in norm(c) for n in names): return c
    return None

def files():
    out = []
    for root in INPUT_DIRS:
        if root.exists():
            out += [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".parquet", ".csv"}]
    return sorted(out)

def read(path):
    return pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path)

def country_from_samplingpoint(v):
    text = str(v).upper()
    m = re.search(r"(?:^|[^A-Z])(NL|BE|DE)(?:[^A-Z]|$)", text)
    return m.group(1) if m else text[:2]

frames, file_summaries = [], []
for path in files():
    try:
        df = read(path)
    except Exception as exc:
        file_summaries.append({"path": str(path), "read_error": repr(exc)})
        continue
    cols = list(df.columns)
    sampling_col = find_col(cols, ["Samplingpoint", "SamplingPoint", "sampling point"])
    pollutant_col = find_col(cols, ["Pollutant", "component", "parameter"])
    start_col = find_col(cols, ["Start", "DatetimeBegin", "begin", "date", "time"])
    value_col = find_col(cols, ["Value", "Concentration", "result"])
    unit_col = find_col(cols, ["Unit"])
    agg_col = find_col(cols, ["AggType", "aggregation", "type", "frequency"])
    country_col = find_col(cols, ["Country", "CountryCode", "country code"])
    city_col = find_col(cols, ["City", "Locality", "municipality"])
    file_summaries.append({"path": str(path), "rows": int(len(df)), "columns": cols,
                           "sampling_col": sampling_col, "pollutant_col": pollutant_col,
                           "start_col": start_col, "value_col": value_col,
                           "agg_col": agg_col, "country_col": country_col, "city_col": city_col})
    if any(c is None for c in [sampling_col, pollutant_col, start_col, value_col]):
        continue
    small = pd.DataFrame()
    small["samplingpoint"] = df[sampling_col].astype(str)
    small["pollutant"] = df[pollutant_col].astype(str)
    small["start"] = pd.to_datetime(df[start_col], errors="coerce", utc=True).dt.tz_convert(None)
    small["value"] = pd.to_numeric(df[value_col], errors="coerce")
    small["unit"] = df[unit_col].astype(str) if unit_col else ""
    small["aggtype"] = df[agg_col].astype(str) if agg_col else ""
    small["country"] = df[country_col].astype(str).str.upper().str[:2] if country_col else small["samplingpoint"].map(country_from_samplingpoint)
    small["city"] = df[city_col].astype(str) if city_col else ""
    frames.append(small)

data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["samplingpoint","pollutant","start","value","unit","aggtype","country","city"])
filtered = data[data["country"].isin(COUNTRIES) & data["pollutant"].str.upper().str.contains("PM10", na=False) & (data["start"] >= START) & (data["start"] <= END) & data["value"].notna()].copy()
if not filtered.empty and filtered["aggtype"].astype(str).str.len().sum() > 0:
    daily = filtered["aggtype"].str.lower().str.contains("day|daily|24h|24 h", na=False)
    if daily.any(): filtered = filtered[daily].copy()

if filtered.empty:
    grouped = pd.DataFrame(columns=["country","city","samplingpoint","observed_days","row_count","first_date","last_date","unit_values","expected_days","coverage_ratio","eligible"])
else:
    filtered["date"] = filtered["start"].dt.date
    grouped = filtered.groupby(["country","city","samplingpoint"], dropna=False).agg(
        observed_days=("date","nunique"), row_count=("value","size"), first_date=("date","min"),
        last_date=("date","max"), unit_values=("unit", lambda x: sorted({str(v) for v in x if str(v)})[:5])
    ).reset_index()
    grouped["expected_days"] = EXPECTED_DAYS
    grouped["coverage_ratio"] = grouped["observed_days"] / EXPECTED_DAYS
    grouped["eligible"] = grouped["coverage_ratio"] >= MIN_COVERAGE
    grouped = grouped.sort_values(["country","city","samplingpoint"], kind="stable")

selected = grouped[grouped["eligible"]].groupby("country", group_keys=False).head(5) if not grouped.empty else grouped.copy()
by_country = {}
for country in sorted(COUNTRIES):
    rows = grouped[grouped["country"] == country]
    sel = selected[selected["country"] == country]
    by_country[country] = {
        "sampling_points_seen": int(rows["samplingpoint"].nunique()) if not rows.empty else 0,
        "eligible_sampling_points": int(rows[rows["eligible"]]["samplingpoint"].nunique()) if not rows.empty else 0,
        "selected_sampling_points": sel["samplingpoint"].tolist(),
        "gate_passed": bool(len(sel) >= 5),
    }

if filtered.empty:
    status, reason = "BLOCKED_SOURCE", "No usable PM10 daily records were parsed under the fixed protocol."
elif all(v["gate_passed"] for v in by_country.values()):
    status, reason = "PASSED_UNDER_PROTOCOL", "All fixed countries have at least five eligible PM10 daily sampling points."
else:
    status, reason = "INSUFFICIENT_COVERAGE", "At least one fixed country has fewer than five eligible PM10 daily sampling points."

grouped.to_csv(OUT_DIR / "station_coverage.csv", index=False)
selected.to_csv(OUT_DIR / "selected_sampling_points.csv", index=False)
summary = {
  "schema": "claimbound_eea_aq_d001_manual_summary_v1",
  "track_id": "EEA_AQ_D001",
  "source": {"name": "EEA Air Quality Download Service", "download_page": "https://aqportal.discomap.eea.europa.eu/download-data/", "web_application": "https://eeadmz1-downloads-webapp.azurewebsites.net/", "api_swagger": "https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html", "raw_payload_committed": False},
  "fixed_scope": {"dataset": "verified E1a", "pollutant": "PM10", "countries": sorted(COUNTRIES), "period": "2018-01-01..2024-12-31", "aggregation": "daily records", "coverage_gate": "at least 85 percent daily coverage per sampling point", "selection_rule": "first five eligible sampling points per country after sorting"},
  "file_summaries": file_summaries,
  "by_country": by_country,
  "result": {"result_status": status, "reason": reason},
  "claim_boundary": {"allowed": "EEA AQ D-001 source-readiness and PM10 daily coverage status under the fixed manual protocol only.", "forbidden": ["air-quality forecasting performance", "deployment readiness", "model superiority", "health-impact claim", "raw payload redistribution"]},
}
(OUT_DIR / "eea_aq_d001_manual_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary["result"], indent=2, sort_keys=True))
PY
```

- [ ] Script created under `$RUN_ROOT/scripts`.
- [ ] I did not edit scope, threshold, countries, pollutant, period, or station-selection rule.

---

## 9. Run And Review

```bash
source "$RUN_ROOT/logs/run_env.sh"
cd "$RUN_ROOT"
. .venv/bin/activate
python scripts/inspect_eea_aq_d001.py
python3 -m json.tool reports/eea_aq_d001_manual_summary.json | less
```

Inspect coverage:

```bash
python - <<'PY'
import pandas as pd, os
root = os.environ["RUN_ROOT"]
coverage = pd.read_csv(f"{root}/reports/station_coverage.csv")
selected = pd.read_csv(f"{root}/reports/selected_sampling_points.csv")
print("Coverage preview:")
print(coverage.head(30).to_string(index=False))
print("\nSelected sampling points:")
print(selected.to_string(index=False))
PY
```

Manual checks:

- [ ] `result.result_status` read.
- [ ] `result.reason` read.
- [ ] `by_country` reviewed.
- [ ] Countries are only `BE`, `DE`, `NL`, or deviation/block reason recorded.
- [ ] Sampling points are not blank, or deviation/block reason recorded.
- [ ] Coverage ratio is plausible: `observed_days / expected_days`.
- [ ] Selected stations follow the fixed sorting rule.
- [ ] I did not change stations or threshold after seeing coverage.

Record final status:

```bash
FINAL_STATUS="$(python3 - <<'PY'
import json, os
root = os.environ["RUN_ROOT"]
with open(f"{root}/reports/eea_aq_d001_manual_summary.json", encoding="utf-8") as f:
    print(json.load(f)["result"]["result_status"])
PY
)"
FINAL_REASON="$(python3 - <<'PY'
import json, os
root = os.environ["RUN_ROOT"]
with open(f"{root}/reports/eea_aq_d001_manual_summary.json", encoding="utf-8") as f:
    print(json.load(f)["result"]["reason"])
PY
)"

cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## Final Manual Status
Result status: $FINAL_STATUS
Reason: $FINAL_REASON
Deviations: none
Known limitations: source-readiness and coverage audit only; no forecasting, health-impact, deployment-readiness, or model-superiority claim
EOF
```

- [ ] Final status recorded.
- [ ] Final reason recorded.
- [ ] Deviations recorded, even if `none`.
- [ ] Limitations recorded.

---

## 10. Blocked Track Path

Use only if access, rights, metadata, timestamps, units, download, or file format prevents a fair run.

```bash
source "$RUN_ROOT/logs/run_env.sh"
BLOCK_REASON="REPLACE_WITH_EXACT_BLOCK_REASON"
python3 - <<PY
import json, os
root = os.environ["RUN_ROOT"]
summary = {
  "schema": "claimbound_eea_aq_d001_manual_summary_v1",
  "track_id": "EEA_AQ_D001",
  "source": {"name": "EEA Air Quality Download Service", "download_page": "https://aqportal.discomap.eea.europa.eu/download-data/", "web_application": "https://eeadmz1-downloads-webapp.azurewebsites.net/", "api_swagger": "https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html", "raw_payload_committed": False},
  "fixed_scope": {"dataset": "verified E1a", "pollutant": "PM10", "countries": ["BE", "DE", "NL"], "period": "2018-01-01..2024-12-31", "aggregation": "daily records", "coverage_gate": "at least 85 percent daily coverage per sampling point", "selection_rule": "first five eligible sampling points per country after sorting"},
  "by_country": {},
  "result": {"result_status": "BLOCKED_SOURCE", "reason": "$BLOCK_REASON"},
  "claim_boundary": {"allowed": "EEA AQ D-001 blocked-source status under the fixed manual protocol only.", "forbidden": ["air-quality forecasting performance", "deployment readiness", "model superiority", "health-impact claim", "raw payload redistribution"]},
}
open(f"{root}/reports/eea_aq_d001_manual_summary.json", "w", encoding="utf-8").write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY

cat >> "$RUN_ROOT/logs/operator_log.md" <<EOF

## Blocked Track Decision
Result status: BLOCKED_SOURCE
Reason: $BLOCK_REASON
Raw payload files committed: no
EOF
```

- [ ] Exact block reason recorded.
- [ ] Blocked summary JSON created.
- [ ] Raw payloads not committed.
- [ ] Blocked result not hidden.

---

## 11. Create Public Artifacts

```bash
source "$RUN_ROOT/logs/run_env.sh"
cd "$CLAIMBOUND_REPO"

git switch -c manual/eea-aq-d001-result
mkdir -p artifacts docs/evidence_cards
cp "$RUN_ROOT/reports/eea_aq_d001_manual_summary.json" artifacts/eea_aq_d001_manual_summary.json

SUMMARY_SHA="$(shasum -a 256 artifacts/eea_aq_d001_manual_summary.json | awk '{print $1}')"
RAW_MANIFEST_SHA="$(awk '{print $1}' "$RUN_ROOT/hashes/raw_payloads_manifest.sha256" 2>/dev/null || printf 'not_available')"
CARD_DATE="$(date -u +%Y-%m-%d)"
CARD_PATH="docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-${CARD_DATE}.json"
STATUS="$(python3 - <<'PY'
import json
with open("artifacts/eea_aq_d001_manual_summary.json", encoding="utf-8") as f: print(json.load(f)["result"]["result_status"])
PY
)"
REASON="$(python3 - <<'PY'
import json
with open("artifacts/eea_aq_d001_manual_summary.json", encoding="utf-8") as f: print(json.load(f)["result"]["reason"])
PY
)"

python3 - <<PY
import json
from pathlib import Path
card = {
  "access_date": "$CARD_DATE",
  "ai_assistance": "not used during manual status decision",
  "baseline_control_summary": "Fixed source-readiness controls: official source, verified E1a dataset, PM10 pollutant, BE/DE/NL country set, daily aggregation, 2018-2024 period, 85 percent coverage gate, first five eligible sampling points per country.",
  "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
  "claim_boundary": "EEA AQ D-001 reports only source-readiness and PM10 daily coverage status under the fixed manual protocol.",
  "claim_type": "source audit",
  "created_at": "$CARD_DATE",
  "domain": "air-quality",
  "evidence_id": "CLAIMBOUND-EEA-AQ-D001-$CARD_DATE",
  "evidence_url": "https://github.com/ClaimBound/claimbound-public-benchmarks/blob/main/$CARD_PATH",
  "execution_mode": "$EXECUTION_MODE",
  "git_commit": "$(git rev-parse --short HEAD)",
  "known_limitations": ["source-readiness and coverage audit only", "no forecasting-performance claim", "no deployment-readiness claim", "no model-superiority claim", "no health-impact claim", "no raw payloads committed"],
  "manual_review": "operator reviewed source access, source rights, raw payload boundary, station selection and final status",
  "official_source_name": "EEA Air Quality Download Service",
  "official_source_url": "https://eeadmz1-downloads-webapp.azurewebsites.net/",
  "operator": "$OPERATOR_NAME",
  "protocol_id": "EEA_AQ_D001",
  "protocol_version": "manual-track-v1",
  "raw_payload_committed": False,
  "raw_payload_manifest": "external raw payload manifest SHA-256: $RAW_MANIFEST_SHA",
  "reproduction_level": "not independently reproduced",
  "result_reason": "$REASON",
  "result_status": "$STATUS",
  "runner_command": "manual runbook docs/manual_audit/EEA_AQ_D001_MANUAL_TRACK.md plus local external inspection script",
  "sanitized_report_path": "artifacts/eea_aq_d001_manual_summary.json",
  "sanitized_report_sha256": "$SUMMARY_SHA",
  "source_rights_note": "Official public EEA source; raw payloads are not committed."
}
Path("$CARD_PATH").write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 -m json.tool "$CARD_PATH" >/tmp/claimbound_card_check.json
if [ -f scripts/claimbound_validate_evidence_card.py ]; then
  uv run --extra dev python scripts/claimbound_validate_evidence_card.py "$CARD_PATH"
fi
```

Create SVG card from the validated JSON:

```bash
SVG_PATH="${CARD_PATH%.json}.svg"
python scripts/claimbound_render_evidence_card_svg.py "$CARD_PATH" "$SVG_PATH"
xmllint --noout "$SVG_PATH"
```

Update `docs/registry/evidence_index.json` manually, then validate:

```bash
python3 -m json.tool docs/registry/evidence_index.json >/tmp/claimbound_registry_check.json
```

- [ ] New branch created.
- [ ] Only sanitized summary copied into `artifacts/`.
- [ ] Evidence card JSON created and validated.
- [ ] SVG rendered from the validated JSON.
- [ ] SVG status matches JSON status.
- [ ] Registry entry and counts updated.
- [ ] Registry JSON validates.

---

## 12. Final Checks And PR

```bash
cd "$CLAIMBOUND_REPO"

if command -v uv >/dev/null 2>&1; then
  uv run --extra dev python -m pytest -n auto
else
  python3 -m pytest -n auto
fi

find . \
  \( -path ./.git -o -path ./.venv -o -path ./.pytest_cache -o -path ./__pycache__ \) -prune \
  -o -type f \
  \( -name '*.csv' -o -name '*.parquet' -o -name '*.zip' -o -name '*.jsonl' -o -name '*.env' -o -name '*.key' -o -name '*.pem' \) \
  -print

rg -n -i "universal forecasting edge|deployment readiness|best model|model superiority|breakthrough|health impact" artifacts docs

git status --short
```

Expected:

- tests pass, or failure is explained in the PR;
- raw-payload scan does not show raw downloaded data;
- broad-claim scan only shows forbidden/limitation contexts;
- `git status --short` shows only intended public files.

Stage and commit:

```bash
git add artifacts/eea_aq_d001_manual_summary.json
git add docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-*.json
git add docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-*.svg
git add docs/registry/evidence_index.json

git status --short
git commit -m "docs: add EEA AQ D-001 manual evidence card"
git push -u origin manual/eea-aq-d001-result
```

PR body:

```text
Summary:
- ran EEA AQ D-001 manual source-readiness track
- added sanitized summary
- added evidence card JSON/SVG
- updated public registry index

Verification:
- protocol lock created before data inspection
- evidence-card JSON validated
- registry JSON validated
- pytest passed, or noted below if unavailable/failed
- raw payload scan clean
- broad-claim scan clean

Raw payload policy:
- raw files stored outside repository
- raw payload manifest hash recorded externally

Result:
- result_status: REPLACE_WITH_FINAL_STATUS
- reason: REPLACE_WITH_FINAL_REASON

Limitations:
- source-readiness and coverage audit only
- no forecasting-performance claim
- no deployment-readiness claim
- no model-superiority claim
- no health-impact claim
```

- [ ] Tests completed or PR explains why not.
- [ ] Raw payload scan clean.
- [ ] Broad claim scan clean or only forbidden-context matches.
- [ ] Only intended public files staged.
- [ ] PR body includes result status, reason, verification, raw-payload policy, and limitations.
- [ ] If checks fail, I will fix only the real issue and will not change the result status to pass checks.

---

## Final Review Before Merge

- [ ] Protocol stayed fixed from the beginning.
- [ ] Protocol lock was hashed before source/data outcome inspection.
- [ ] Raw payloads stayed outside the repository.
- [ ] Source-rights note is honest.
- [ ] Selected stations follow the sorting rule.
- [ ] Coverage uses the fixed 85 percent threshold.
- [ ] Public summary avoids raw payload details.
- [ ] Evidence card validates.
- [ ] SVG matches JSON card.
- [ ] Registry index points to the right card.
- [ ] Final claim stays inside source-readiness and coverage only.
- [ ] Insufficient, blocked, or negative result is recorded without shame.
- [ ] If passed, limitations are still visible.

---

## What To Share After Merge

Share:

- pull request;
- sanitized summary JSON;
- evidence card JSON;
- evidence card SVG;
- registry index entry.

Do not share:

- raw parquet files;
- raw ZIP files;
- raw source CSV files;
- browser screenshots with local paths;
- private notes;
- tokens, keys, local env files;
- claims outside this protocol.
