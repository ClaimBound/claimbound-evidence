# Release Process

Use this process when publishing a ClaimBound release or patch release.

## Pre-Release Checks

Run:

```bash
uv sync --extra dev
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Check manually:

- no raw payloads, transcripts, credentials or private data are committed;
- artifact-only records are not presented as validated evidence cards;
- public cards have narrow claim boundaries and forbidden-claim wording;
- source-audit cards do not imply model safety, model quality, runtime behavior
  or deployment readiness;
- registry entries point to validated card JSON;
- generated SVG previews were rendered from JSON and not edited by hand after
  outcome inspection.

## Release Notes

Release notes should state:

- what changed;
- which validators or protocols changed;
- which cards or examples were added;
- whether any status semantics changed;
- which limitations remain.

Do not describe scaffolds, requests or future plans as completed evidence.

## Version Boundary

Use patch releases for documentation, validator and card fixes that do not
change public semantics. Use minor releases when schemas, workflow rules,
registry structure or status interpretation materially change.

## After Release

- Sync `pyproject.toml`, `specs/repo_version.yaml`, `docs/assets/badge_release.svg`
  and [CHANGELOG](CHANGELOG.md) with the GitHub tag.
- Update README badges or release links when needed.
- Keep old cards citable unless they are invalid; if invalid, mark the problem
  explicitly rather than silently rewriting history.
- Open follow-up issues for unresolved validator, registry, rerun or source
  drift work.

