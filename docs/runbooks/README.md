# Operator Runbooks

Step-by-step playbooks for open external-operator issues.

| Issue | Playbook |
| --- | --- |
| #55 NASA POWER D-103 rerun | [ISSUE_55_NASA_RERUN_PLAYBOOK.md](ISSUE_55_NASA_RERUN_PLAYBOOK.md) |
| #56 NOAA CO-OPS D-131 negative rerun | [ISSUE_56_NOAA_RERUN_PLAYBOOK.md](ISSUE_56_NOAA_RERUN_PLAYBOOK.md) |
| #57 EEA source drift check | [ISSUE_57_EEA_DRIFT_PLAYBOOK.md](ISSUE_57_EEA_DRIFT_PLAYBOOK.md) |
| #58 AI source-audit boundary review | [ISSUE_58_AI_BOUNDARY_PLAYBOOK.md](ISSUE_58_AI_BOUNDARY_PLAYBOOK.md) |
| #59 Developer evidence card | [ISSUE_59_API_PARITY_PLAYBOOK.md](ISSUE_59_API_PARITY_PLAYBOOK.md) |

Shared setup (works in **zsh** and bash on macOS):

```bash
export REPO_ROOT="<absolute-path-to-claimbound-evidence-checkout>"
export RUNS_ROOT="$HOME/claimbound_runs"
export OPERATOR="<your-handle>"
export TODAY="$(date +%F)"

cd "$REPO_ROOT"
uv sync --extra dev
uv run claimbound validate-all
```

Capture `run-root` directory (first stdout line):

```bash
export RUN_DIR="$(
  uv run claimbound run-root \
    --protocol-id "PROTOCOL_ID" \
    --source-url "https://example.org/source" \
    --operator "$OPERATOR" \
    --root "$RUNS_ROOT" | head -1
)"
echo "RUN_DIR=$RUN_DIR"
```
