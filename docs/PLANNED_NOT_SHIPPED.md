# Planned Work Not Shipped Yet

This page lists public roadmap items that are **not** claimed as completed in
the current repository. It prevents reviewers from treating design documents or
roadmap rows as shipped product.

## How To Read The Public Roadmap

[Public roadmap 2026](ROADMAP_2026.md) describes planned hardening work.
Acceptance-criteria documents are specifications only until implementation lands
and validators pass on `main`.

| Planned item | What exists now | What is not shipped | How to verify honestly |
| --- | --- | --- | --- |
| SourceProbe v1 | Scaffold stub in `claimbound new`; [acceptance criteria](SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md) | Deterministic HTTP probe CLI, marker checks, standalone probe command | Read the spec; confirm no `scripts/claimbound_source_probe.py` |
| Static registry MVP | JSON index at [evidence_index.json](registry/evidence_index.json) | Generated HTML/views, filters UI, `claimbound_build_registry_view.py` | Read [acceptance criteria](STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md); confirm no `docs/registry/views/` |
| PyPI distribution | Local install via `uv sync` from git | Published package on PyPI | No `claimbound-evidence` release wheel on PyPI required for current baseline |
| WCAG / accessibility pass | SVG cards rendered from JSON | Full accessibility audit and remediation pass | Cards are visual aids; no WCAG conformance claim is made |

## What Counts As Shipped Today

The current public baseline is:

- evidence-card JSON/SVG and registry index;
- `uv run claimbound validate-all` and pytest gates;
- manual and AI-assisted workflow docs;
- public runners for existing card types (EEA, NASA, NOAA, public AI docs, etc.);
- rerun workflow docs, issue templates and maintainer rerun examples.

## Artifact-Only Records Are Not Missing Cards By Accident

Some runs produced useful sanitized summaries without full card promotion. They
are listed in the [artifacts catalog](artifacts/README.md) and must not be cited
as registry cards:

- NYC TLC Phase 4 negative artifact;
- CDC mirror blocked-source artifact.

Validated blocked cards such as [CIVIC_CLAIM_D001](evidence_cards/CLAIMBOUND-CIVIC_CLAIM_D001-2026-05-07.json)
are separate records with explicit `BLOCKED_SOURCE` status.

## Advanced Optional Registry Card

[PROGRAM_FIT_D001](evidence_cards/CLAIMBOUND-PROGRAM_FIT_D001-2026-06-04.json)
remains in the registry as an **advanced optional** methodology demo. It is not
a first-screen example and does not prove program approval or endorsement.