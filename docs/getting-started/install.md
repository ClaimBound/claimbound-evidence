# Install

Protocolith needs Python 3.11 to 3.15 and nothing else: the package has no required dependencies, no compiled
code and no network access. It runs headless on macOS, Linux and Windows.

## Status of the packages

| Route | State |
| --- | --- |
| From a source checkout with `uv sync` | Works today. |
| `pip install protocolith` | Planned for the 0.6.0 release. Until it is published, use the source checkout. |
| conda-forge | Planned, no date. |

The version in `pyproject.toml` is still 0.5.0; the ledger commands are part of the 0.6.0 work and are on the
development branch.

## From source, per operating system

Install [uv](https://docs.astral.sh/uv/) once, then clone and sync. `uv sync` creates `.venv` inside the checkout.

| OS | Get uv | Activate the environment |
| --- | --- | --- |
| macOS | `brew install uv` or the installer from the uv documentation | `source .venv/bin/activate` |
| Linux | the installer from the uv documentation, or your package manager | `source .venv/bin/activate` |
| Windows (PowerShell) | `winget install astral-sh.uv` or the installer from the uv documentation | `.venv\Scripts\Activate.ps1` |
| Windows (cmd) | same | `.venv\Scripts\activate.bat` |

```bash
git clone https://github.com/protocolith/protocolith.git
cd protocolith
uv sync
uv run protocolith --version
```

Without uv, any Python 3.11 to 3.15 works:

```bash
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -e .
protocolith --version
```

`uv sync --extra dev` adds the test tools (pytest, ruff and others) used in [testing](../development/testing.md).

## The two program names

`protocolith` and `plith` are the same program.

## What works where

| Feature | macOS | Linux | Windows |
| --- | --- | --- | --- |
| freeze, record, deviation, verify-ledger, issue, log, head, repair | yes | yes | yes |
| MCP server on stdio | yes | yes | yes |
| Append lock | `fcntl.flock` | `fcntl.flock` | `msvcrt.locking` |

The two lock modules each run only on their own platform; the project CI runs the tests on Linux, Windows and
macOS (see `.github/workflows/tests.yml`). Newlines in the ledger are always `\n`, on Windows too.

## Check the install

```bash
protocolith --version
protocolith freeze --help
```

Then continue with [your first record](first-record.md).

## Older card commands

The package still contains the evidence-card tools of earlier releases (`validate-card`, `inspect`, `hash`,
`doctor`, `validate-all` and others). Some need a repository clone because they read cards and runner scripts
that are not part of the package; see the [command reference](../CLI.md) and the
[archive](../archive/README.md).
