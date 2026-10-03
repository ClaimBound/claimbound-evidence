# Building from source and managing dependencies

## Build instructions

Requirements: Python 3.12 or newer and [uv](https://docs.astral.sh/uv/). Nothing else is needed:
the package is pure Python, with no compiler, SDK or system library.

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev          # creates .venv with the locked dependencies
uv run claimbound doctor     # checks the environment
uv build                     # builds the sdist and the wheel into dist/
uvx twine check dist/*       # checks the package metadata
```

The build backend is `hatchling` with `hatch-fancy-pypi-readme`, declared in `pyproject.toml`
under `[build-system]`; installers fetch them automatically. Without uv, `python -m build`
also builds the package. Run the tests with `uv run pytest -n auto`.

## How dependencies are selected, obtained and tracked

**Selecting.** The package keeps a short runtime dependency list (`numpy`, `pdfplumber`,
`pypdf`, declared in `pyproject.toml`). A dependency is added only when it is needed, is
released under a FLOSS license, is published on PyPI and is packaged on conda-forge.
Development tools (pytest, ruff, build tools) are optional extras and are not installed
for users.

**Obtaining.** Dependencies come only from PyPI. Exact versions and file hashes are locked
in `uv.lock`, which `uv sync` uses. The release workflow installs its build tools with
`pip install --require-hashes` from `.github/requirements/publish.txt`. GitHub Actions are
pinned to full commit SHAs and the Docker base image is pinned by digest.

**Tracking.** Dependabot opens update pull requests for `uv`, `pip`, `github-actions` and
`docker` (`.github/dependabot.yml`). Every pull request runs the `dependency-review`
workflow (fails on high severity) and CodeQL; GitHub Dependabot alerts are enabled; and
the `scorecard` workflow publishes supply-chain checks. A vulnerable dependency is updated
through the same pull-request process as any other change.
