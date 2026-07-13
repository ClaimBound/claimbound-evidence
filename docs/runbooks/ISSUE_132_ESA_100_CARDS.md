# ESA issue #132 100-card batch runbook

Issue #132 is represented by a frozen 100-protocol ESA-only source-boundary matrix:

- Sentinel-6: `ESA-S6-01-D301` through `ESA-S6-20-D320`
- EarthCARE: `ESA-ECARE-01-D321` through `ESA-ECARE-20-D340`
- Biomass: `ESA-BIOMASS-01-D341` through `ESA-BIOMASS-20-D360`
- FLEX: `ESA-FLEX-01-D361` through `ESA-FLEX-20-D380`
- Swarm: `ESA-SWARM-01-D381` through `ESA-SWARM-20-D400`

The runner never forces all cards green. Each frozen gate records one honest status:

- `PASSED_UNDER_PROTOCOL`
- `INSUFFICIENT_COVERAGE`
- `BLOCKED_SOURCE`

Raw ESA HTML stays under `~/claimbound_runs/` and is not committed.

## 1. Prepare the checkout

```bash
cd <path-to-claimbound-evidence-checkout>
uv sync --extra dev
uv run claimbound doctor
```

Review local changes before running a batch workflow:

```bash
git status --short
```

## 2. Validate the committed state

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
uv run python scripts/claimbound_run_esa_issue_132.py check
```

Expected matrix output:

```text
matrix_cards=100
matrix_status=VALID
```

Confirm that all 100 issue #132 protocols are present in the registry:

```bash
python3 - <<'PY'
import json
from pathlib import Path

registry = json.loads(
    Path("docs/registry/evidence_index.json").read_text(encoding="utf-8")
)

expected = set()
for prefix, start in [
    ("S6", 301),
    ("ECARE", 321),
    ("BIOMASS", 341),
    ("FLEX", 361),
    ("SWARM", 381),
]:
    for slot in range(1, 21):
        expected.add(f"ESA-{prefix}-{slot:02d}-D{start + slot - 1}")

present = {row.get("protocol_id") for row in registry["cards"]}
missing = sorted(expected - present)

print("expected_issue_132_cards =", len(expected))
print("registered_issue_132_cards =", len(expected & present))
print("missing =", missing)

assert not missing
PY
```

## 3. Create a local-only preview

The preview fetches ESA public pages into the local run root, evaluates the frozen matrix and writes a reviewable JSON summary. It does not create repository evidence cards.

```bash
PREVIEW="$(
  uv run python scripts/claimbound_run_esa_issue_132.py \
    preview --quiet
)"

echo "$PREVIEW"
test -f "$PREVIEW"
```

Inspect the preview:

```bash
uv run claimbound inspect json "$PREVIEW" \
  --keys issue_number access_date result_counts claim_boundary
```

Print every non-pass result before publication:

```bash
python3 - "$PREVIEW" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

non_pass = [
    row for row in data["results"]
    if row["result_status"] != "PASSED_UNDER_PROTOCOL"
]

print("non_pass_count =", len(non_pass))
for row in non_pass:
    print()
    print(row["protocol_id"], row["result_status"])
    print("claim:", row["claim"])
    print("missing_patterns:", row["missing_patterns"])
    if row.get("block_reason"):
        print("block_reason:", row["block_reason"])
PY
```

The preview freezes:

- the 100 claim gates;
- the five source hashes;
- the access date;
- all pass, insufficient-coverage and blocked results.

## 4. Publish after review

Run publication only after reading the preview:

```bash
uv run python scripts/claimbound_run_esa_issue_132.py publish \
  --preview "$PREVIEW" \
  --operator "<your-github-handle>" \
  --confirm-reviewed
```

The command writes or refreshes ESA issue #132 evidence outputs, the registry and the batch report. Existing target cards are detected instead of duplicated.

## 5. Validate generated evidence

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Inspect the committed batch report:

```bash
uv run claimbound inspect json \
  artifacts/esa_issue_132_batch_summary.json \
  --keys issue_number access_date operator result_counts claim_boundary
```

Raw HTML must not appear in the repository:

```bash
if git status --short | grep -Eq '\.html$|/raw/'; then
  echo "ERROR: raw ESA payload is inside the repository"
  false
else
  echo "OK: no raw ESA HTML is inside the repository"
fi
```

## 6. Review before commit

```bash
git status --short
git diff --stat
git diff -- docs/registry/evidence_index.json
```

Then rerun:

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```
