# Release process

The checklist that maintainers follow is in [RELEASE_PROCESS.md](../../RELEASE_PROCESS.md). This page summarises
the shape of a release and says which parts are done by hand.

## Rules

- A release, a tag, a GitHub release and a PyPI or TestPyPI upload happen only after explicit approval by the
  repository owner, each time.
- History of published branches is never rewritten, and `main` is never force-pushed.
- Version `1.0.0` is reserved until an independent external rerun exists and a second implementation passes the
  [conformance vectors](../reference/conformance-vectors.md).

## Steps

1. Sync the version in `pyproject.toml`, `docs/assets/badge_release.svg`, `specs/repo_version.yaml` and the
   changelog.
2. Run the checks:
   ```bash
   uv sync --extra dev
   uv run ruff check src tests
   uv run --extra dev pytest -q -n auto
   uv run python scripts/gen_cli_reference.py --check
   uv build && uvx twine check dist/*
   ```
3. Build the documentation (`uv run --extra docs python scripts/build_docs_site.py`, then
   `uv run --extra docs mkdocs build --strict`).
4. Tag and publish through the protected workflow, after approval. PyPI publication uses Trusted Publishing from
   that workflow.
5. Write the release notes: what changed, what is planned and not shipped, known limits.

## 0.6.0

The 0.6.0 release (2026-11-16) shipped the core ledger commands, the specification and the conformance vectors, and made
`pip install protocolith` available from PyPI, with a Zenodo DOI.

## 0.7.0

The 0.7.0 release adds anchoring of the ledger head, `claim-check`, the MCP research prompt and selective disclosure. Before
tagging: bump the version in `pyproject.toml`, `CITATION.cff`, `specs/repo_version.yaml` and `core/mcp.py`; rebuild the examples
whose anchors record the version (`examples/phantom_mean_reversion/build_ledger.py`, `scripts/build_disclosure_demo.py`); then
tag and publish through the protected workflow.
