# Sustainability And Maintenance

ClaimBound is a single-maintainer open-source foreground project. This page
describes how the repository is intended to remain usable without becoming a
hosted certification service.

## What stays in scope

- Evidence-card validators and tests.
- Public registry JSON and rendered SVG previews.
- Manual and AI-assisted operator runbooks.
- Honest example cards (positive, negative, blocked, drift).
- Documentation for external operators and reruns.

## What stays out of scope

- Hosted accounts, authenticated write APIs or Postgres registries.
- Legal certification, procurement approval or model safety guarantees.
- Raw payload archives when redistribution is unclear.
- Closed proprietary systems bundled into the public repository.

## Release cadence

| Change type | Version bump | Example |
| --- | --- | --- |
| Docs, card wording, registry metadata | patch | v0.4.1 |
| New validated cards, workflow rules | minor | v0.4.0 |
| Schema or status semantics change | minor/major with migration notes | v1.0.0 |

See [RELEASE_PROCESS.md](../RELEASE_PROCESS.md).

## Community and reruns

Sustainability depends on **external reruns and feedback**, not vanity metrics:

- reproduction request issues;
- GitHub Discussions for card requests;
- independent operators following [examples/rerun](../examples/rerun/README.md).

Public CI on GitHub Actions (`pytest` on every push and pull request) uses
free hosted runners for this open repository.

## Post-funding maintenance (if approved)

A funded 9-month work package would add SourceProbe v1, static registry views and
additional honest cards — still without a hosted backend. See
[ROADMAP_2026.md](ROADMAP_2026.md).

## Maintainer boundary

The maintainer publishes protocols and examples; third parties run their own
checks locally. See [MAINTAINER_BOUNDARY.md](../MAINTAINER_BOUNDARY.md).
