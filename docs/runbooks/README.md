# Operator Runbooks

Step-by-step playbooks for open external-operator issues.

| Issue | Playbook |
| --- | --- |
| #55 NASA POWER D-103 rerun | [ISSUE_55_NASA_RERUN_PLAYBOOK.md](ISSUE_55_NASA_RERUN_PLAYBOOK.md) |
| #56 NOAA CO-OPS D-131 negative rerun | [ISSUE_56_NOAA_RERUN_PLAYBOOK.md](ISSUE_56_NOAA_RERUN_PLAYBOOK.md) |
| #57 EEA source drift check | [ISSUE_57_EEA_DRIFT_PLAYBOOK.md](ISSUE_57_EEA_DRIFT_PLAYBOOK.md) |
| #58 AI source-audit boundary review | [ISSUE_58_AI_BOUNDARY_PLAYBOOK.md](ISSUE_58_AI_BOUNDARY_PLAYBOOK.md) |
| #59 Developer evidence card | [ISSUE_59_API_PARITY_PLAYBOOK.md](ISSUE_59_API_PARITY_PLAYBOOK.md) |

Shared setup (Windows, macOS and Linux via the `claimbound` CLI):

```bash
cd <path-to-claimbound-evidence-checkout>
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
```

Use your GitHub handle as `--operator` and note today's date for issue
comments (`claimbound doctor` prints `today=YYYY-MM-DD`). See
[platform support](../PLATFORM_SUPPORT.md).

Create a run directory (first printed line is the path to reuse):

```bash
uv run claimbound run-root \
  --protocol-id "PROTOCOL_ID" \
  --source-url "https://example.org/source" \
  --operator "<your-handle>"
```
