# VERIFY Issue Closing Comment Template

Copy into the VERIFY issue you completed. Replace placeholders.

```markdown
## External verification report

- Operator: OPERATOR_HANDLE
- Date: YYYY-MM-DD
- Repo commit: `FULL_SHA`
- Pack: Tier A | Tier B | Tier C (NASA) | Tier C (NOAA)
- Environment: OS + Python version

### Baseline
- [ ] `uv run claimbound validate-all` → exit 0, `valid_cards=24`
- [ ] `uv run --extra dev python -m pytest -q` → 72 passed

### Pack-specific checks
- [ ] <list commands you ran and outcomes>

### Outcome
- Result: match | mismatch | spec-only
- Source-byte drift observed: yes | no | n/a
- Claim boundary OK: yes | no | n/a

### Limitations
- Single-operator verification only.
- No raw payloads committed to the repository.
- No certification, deployment readiness or model-safety claims.

### Recommendation
Close this VERIFY issue as completed under the narrow checklist above.
```