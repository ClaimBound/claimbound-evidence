# Maintainer Guide (Public)

Single-maintainer open-source boundary for ClaimBound. This is not a hosted
review service or certification authority.

## Daily health checks

```bash
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

Expected: `ready=yes`, `valid_cards=37`, `86 passed`.

## What you may merge

- Validator fixes with tests.
- Evidence cards that pass `validate-all` with narrow `claim_boundary` text.
- Documentation that distinguishes shipped vs planned work.
- Maintainer `SINGLE_OPERATOR_RERUN` cards when honestly labeled.

## What requires external signal

- Closing VERIFY Tier C issues as **independent** evidence: operator must not be
  `maintainer`.
- Upgrading `verification_level` to `INDEPENDENT_RERUN` or `MULTI_OPERATOR`.

See [External verification packs](external_verification/README.md) and
[Independent rerun workflow](INDEPENDENT_RERUN_WORKFLOW.md).

## Release process

Follow [Release process](../RELEASE_PROCESS.md). Sync `pyproject.toml`,
`specs/repo_version.yaml`, `docs/assets/badge_release.svg`, CHANGELOG and GitHub
release tag.

## Bus-factor controls

Published in public:

- [Governance](../GOVERNANCE.md)
- [Maintainer boundary](../MAINTAINER_BOUNDARY.md)
- [Release process](../RELEASE_PROCESS.md)
- Reproducible operator runbooks under [docs/runbooks/](runbooks/README.md)
- [Planned work not shipped](PLANNED_NOT_SHIPPED.md)

## Do not imply in public materials

- Program endorsement or award likelihood (see PROGRAM_FIT_D001 limits).
- Shipped SourceProbe, static registry UI or PyPI when only specs exist.
- Model safety, runtime behavior or benchmark superiority from source-audit cards.
