# Platform Support

ClaimBound workflows run on **Windows**, **macOS** and **Linux** through the
`claimbound` Python CLI. You do not need bash, jq, curl or shasum for the
documented primary operator paths.

## Prerequisites

| Tool | Required | Notes |
| --- | --- | --- |
| Python | Yes | Version 3.12 or newer |
| git | Yes | Clone the repo; `demo grok-source-audit` clones a public repo locally |
| uv | Recommended | Fastest install path from the repository checkout |
| pip | Alternative | `pip install -e ".[dev]"` from the repo root also works |

Check your machine:

```bash
uv run claimbound doctor
```

Expected: `python=ok`, `git=ok`, `repo_layout=ok`, `ready=yes`.

## Install (any OS)

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
```

Without `uv`:

```bash
pip install -e ".[dev]"
claimbound doctor
claimbound validate-all
```

## Local run directories

`claimbound run-root` creates timestamped folders under your home directory:

```text
<home>/claimbound_runs/<protocol>_<timestamp>/
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
uv run claimbound run-root \
  --protocol-id "EXAMPLE_D001" \
  --source-url "https://example.org/source" \
  --operator "your-handle" \
  --root "C:/Users/you/claimbound_runs"
```

The first line printed by `run-root` is the new run directory path. Copy it for
rerun workflows.

## What is cross-platform today

| Workflow | Command | OS notes |
| --- | --- | --- |
| Validate registry | `claimbound validate-all` | Pure Python |
| Create scaffold | `claimbound new` | Interactive prompts work in any terminal |
| Local run root | `claimbound run-root` | Uses `Path.home()` by default |
| Demos | `claimbound demo eea-source-audit` | Python HTTP; no curl required |
| Environment check | `claimbound doctor` | Confirms Python, git and repo layout |

| Inspect JSON fields | `claimbound inspect card/registry/json` | Replaces jq |
| File hashes | `claimbound hash` | Replaces shasum |

`claimbound rerun`, `drift` and `verify` commands land in follow-up PRs.

## Optional shell tools

Bash one-liners in some runbooks remain as **optional advanced** paths for
operators who already use a Unix shell. They are not required to close VERIFY
issues when the matching `claimbound` command exists.

## CI coverage

GitHub Actions runs `validate-all` and pytest on Linux and Windows. See
`.github/workflows/tests.yml`.

## Related docs

- [Getting started](GETTING_STARTED.md)
- [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md)
- [External verification packs](external_verification/README.md)