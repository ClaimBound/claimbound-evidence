# Issue #59 Playbook — Developer evidence card (API_PARITY_D001)

Goal: add one narrow software-development evidence card beyond AI/docs examples.

Pattern: copy `SOFTWARE_DEV_D001`, change the frozen claim to registry parity.

## Read first

- `docs/protocols/SOFTWARE_DEV_D001_PREREG_CHARTER.md`
- `docs/evidence_cards/CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json`
- `artifacts/software_dev_d001_summary.json`
- `docs/SOFTWARE_DEVELOPMENT_WORKFLOW.md`

## 1. Freeze protocol before run

Create `docs/protocols/API_PARITY_D001_PREREG_CHARTER.md` with a claim like:

```text
Under frozen API_PARITY_D001, registry validation exits 0 and reports the
expected registry_name and card_count for the committed index.
```

Forbidden: production readiness, security certification, total correctness.

## 2. Manual audit folder

```bash
cd "$REPO_ROOT"
mkdir -p docs/manual_audit/API_PARITY_D001

cp docs/manual_audit/SOFTWARE_DEV_D001/SOFTWARE_DEV_D001_PLAYBOOK.md \
   docs/manual_audit/API_PARITY_D001/API_PARITY_D001_PLAYBOOK.md
cp docs/manual_audit/SOFTWARE_DEV_D001/SOFTWARE_DEV_D001_CHECKLIST.md \
   docs/manual_audit/API_PARITY_D001/API_PARITY_D001_CHECKLIST.md
cp docs/manual_audit/SOFTWARE_DEV_D001/SOFTWARE_DEV_D001_OPERATOR_DECLARATION.md \
   docs/manual_audit/API_PARITY_D001/API_PARITY_D001_OPERATOR_DECLARATION.md
```

Edit copied files: replace `SOFTWARE_DEV_D001` → `API_PARITY_D001` and commands below.

## 3. Frozen commands (run exactly)

Primary path (any OS):

```bash
uv run claimbound validate-all
uv run claimbound inspect registry --keys registry_name card_count registry_version
```

`validate-all` must exit `0`. Record `git rev-parse HEAD` in your summary if you
use git.

## 4. Sanitized summary

```bash
cat > artifacts/api_parity_d001_summary.json <<EOF
{
  "protocol_id": "API_PARITY_D001",
  "evidence_id": "CLAIMBOUND-API_PARITY_D001-${TODAY}",
  "access_date": "${TODAY}",
  "claim_boundary": "Records registry validation parity only under frozen commands.",
  "execution_mode": "MANUAL_NO_AI",
  "operator": "${OPERATOR}",
  "official_sources": [
    {
      "name": "ClaimBound evidence repository",
      "url": "https://github.com/ClaimBound/claimbound-evidence",
      "git_commit": "${GIT_SHA}"
    }
  ],
  "checked_claim": "Registry validator passes and registry metadata matches frozen expectation.",
  "frozen_commands": [
    "uv run python scripts/claimbound_validate_registry.py",
    "uv run claimbound validate-all"
  ],
  "gate_results": [
    {"gate": "validate_registry", "result": "PASS"},
    {"gate": "validate_all", "result": "PASS"}
  ],
  "expected_registry_name": "${EXPECTED_REGISTRY_NAME}",
  "expected_card_count": ${EXPECTED_CARD_COUNT},
  "known_limitations": [
    "Single-operator check only.",
    "Registry metadata parity only."
  ]
}
EOF

export REPORT_SHA="$(shasum -a 256 artifacts/api_parity_d001_summary.json | awk '{print $1}')"
echo "REPORT_SHA=$REPORT_SHA"
```

## 5. Evidence card JSON

Copy `docs/evidence_cards/CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11.json` to
`docs/evidence_cards/CLAIMBOUND-API_PARITY_D001-${TODAY}.json` and update:

| Field | Value |
| --- | --- |
| `evidence_id` | `CLAIMBOUND-API_PARITY_D001-${TODAY}` |
| `protocol_id` | `API_PARITY_D001` |
| `registry_sequence` | next free integer in `docs/registry/evidence_index.json` |
| `record_type` | `evidence_result` |
| `result_status` | `PASSED_UNDER_PROTOCOL` |
| `sanitized_report_path` | `artifacts/api_parity_d001_summary.json` |
| `sanitized_report_sha256` | `$REPORT_SHA` |
| `git_commit` | short SHA |
| `operator` | `$OPERATOR` |

Render SVG:

```bash
uv run --extra dev python scripts/claimbound_render_evidence_card_svg.py \
  "docs/evidence_cards/CLAIMBOUND-API_PARITY_D001-${TODAY}.json" \
  "docs/evidence_cards/CLAIMBOUND-API_PARITY_D001-${TODAY}.svg"
```

## 6. Registry + validation

Add entry to `docs/registry/evidence_index.json`, increment `card_count`, update
`statistics`, then:

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -n auto -q
```

Closes #59.
