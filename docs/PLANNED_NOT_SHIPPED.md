# Planned Work Not Shipped Yet

This page lists public roadmap items that are **not** claimed as completed in
the current repository. It prevents reviewers from treating design documents or
roadmap rows as shipped product.

## How To Read The Public Roadmap

[Public roadmap 2026](ROADMAP_2026.md) describes planned hardening work.
Acceptance-criteria documents are specifications only until implementation lands
and validators pass on `main`.

| Planned item | Status in 0.5.0 | What is still not shipped |
| --- | --- | --- |
| SourceProbe v1 | Shipped: `claimbound probe`, [SOURCE_PROBE.md](SOURCE_PROBE.md) | Live probing of every registry source; probes are metadata, never evidence |
| Static registry MVP | Shipped: [views](registry/views/index.md), [REGISTRY_VIEWS.md](REGISTRY_VIEWS.md) | Audience filter (no audience field in cards yet) |
| Run-root deviation log, rerun report, public AI protocol, scaffold hardening | Shipped (see CHANGELOG 0.5.0) | Operator adoption; no external rerun has been reported yet |
| PyPI distribution | Package `claimbound-evidence` on PyPI with the card-level CLI; full workflows via `git clone` + `uv sync` | Registry, runners, reruns and demos inside the pip package |
| WCAG / accessibility | Renderer emits accessible SVG; linter reports gaps ([ACCESSIBILITY.md](ACCESSIBILITY.md)) | Regeneration of the ~8000 committed SVGs; no conformance claim |
| New honest card set, v1.0.0 | Not started | Cards need frozen protocols and a fresh fetch; v1.0.0 waits for an external rerun |

## What Counts As Shipped Today

The current public baseline is:

- evidence-card JSON/SVG and registry index;
- `uv run claimbound validate-all` and pytest gates (CI on Linux, Windows and macOS);
- cross-platform operator CLI: `doctor`, `inspect`, `hash`, `rerun`, `drift`, `verify`;
- [platform support](PLATFORM_SUPPORT.md) and [start without coding](START_WITHOUT_CODING.md);
- manual and AI-assisted workflow docs;
- public runners for existing card types (EEA, NASA, NOAA, public AI docs, etc.);
- rerun workflow docs, issue templates and maintainer rerun examples.

The [ESA 500-card evidence atlas](esa/ESA_500_HEATMAP.md) is a shipped,
campaign-specific static visualization. It does not implement the planned
general-purpose registry MVP, registry search, or generated cross-track views.

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
