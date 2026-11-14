# Platform Support

Protocolith workflows run on **Windows**, **macOS** and **Linux** through the
`protocolith` Python CLI. You do not need bash, jq, curl or shasum for the
documented primary operator paths.

## Prerequisites

| Tool | Required | Notes |
| --- | --- | --- |
| Python | Yes | Version 3.11 or newer (tested 3.11 to 3.15) |
| git | Yes | Clone the repo; `demo grok-source-audit` clones a public repo locally |
| uv | Recommended | Fastest install path from the repository checkout |
| pip | Alternative | `pip install -e ".[dev]"` from the repo root also works |

Check your machine:

```bash
uv run protocolith doctor
```

Expected: `python=ok`, `git=ok`, `repo_layout=ok`, `ready=yes`.

## Install (any OS)

```bash
git clone https://github.com/protocolith/protocolith.git
cd protocolith
uv sync --extra dev
uv run protocolith doctor
uv run protocolith validate-all
```

Without `uv`:

```bash
pip install -e ".[dev]"
protocolith doctor
protocolith validate-all
```

## Local run directories

`protocolith run-root` creates timestamped folders under your home directory:

```text
<home>/protocolith_runs/<protocol>_<timestamp>/
  raw/
  logs/
  hashes/
  reports/
  transcripts/
```

On Windows the home directory is your user profile folder. The CLI uses
`pathlib` and does not require `$HOME` or `%USERPROFILE%` in commands.

Override the parent directory when needed:

```bash
uv run protocolith run-root \
  --protocol-id "EXAMPLE_D001" \
  --source-url "https://example.org/source" \
  --operator "your-handle" \
  --root "C:/Users/you/protocolith_runs"
```

The first line printed by `run-root` is the new run directory path. Copy it for
rerun workflows.

## What is cross-platform today

| Workflow | Command | OS notes |
| --- | --- | --- |
| Validate registry | `protocolith validate-all` | Pure Python |
| Create scaffold | `protocolith new` | Interactive prompts work in any terminal |
| Local run root | `protocolith run-root` | Uses `Path.home()` by default |
| Demos | `protocolith demo eea-source-audit` | Python HTTP; no curl required |
| Environment check | `protocolith doctor` | Confirms Python, git and repo layout |
| Inspect JSON fields | `protocolith inspect card/registry/json` | Replaces jq |
| File hashes | `protocolith hash` | Replaces shasum |
| NASA / NOAA reruns | `protocolith rerun nasa-d103` / `noaa-d131` | Python download + gate |
| EEA drift | `protocolith drift eea-source-audit` | Probe + field compare |
| VERIFY packs | `protocolith verify starter-pack` (etc.) | Tier A/B/C checklist shortcuts |

## Optional shell tools

Bash one-liners in some runbooks remain as **optional advanced** paths for
operators who already use a Unix shell. They are not required to close VERIFY
issues when the matching `protocolith` command exists.

## CI coverage

GitHub Actions runs `validate-all` and pytest on Linux and Windows. See
`.github/workflows/tests.yml`.

## Related docs

- [Getting started](GETTING_STARTED.md)
- [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md)
- [External verification packs](external_verification/README.md)