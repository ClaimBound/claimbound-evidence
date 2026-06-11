# Changelog

## 0.4.4 - 2026-06-11

### Fixed

- Evidence-card SVG renderer now uses inline text attributes so cards render in
  GitHub README `<img>` embeds (GitHub strips internal `<style>` blocks).
- Clarified SOFTWARE_DEV_D001 allowed claim: regression gate passed, validator
  rejects missing `execution_mode`.

### Changed

- Moved SVG render logic to `claimbound_evidence.card_svg_render`; regenerated
  all committed evidence-card SVG files.

## 0.4.3 - 2026-06-11

### Added

- Software development workflow: where/how ClaimBound was used, strengths, and
  counterfactual without ClaimBound; track pattern examples split to companion doc.

### Changed

- `docs/SOFTWARE_DEVELOPMENT_WORKFLOW.md` expanded with completed in-repo and
  external case-study usage narrative.

## 0.4.2 - 2026-06-11

### Changed

- Embed the `SOFTWARE_DEV_D001` evidence card SVG in README, software
  development workflow, case study page and current tracks summary.

## 0.4.1 - 2026-06-11

### Changed

- Cross-linked the public
  [software-rnd-evidence-case-study](https://github.com/ClaimBound/software-rnd-evidence-case-study)
  repository (v1.0.0) from README and case study page.
- Removed staging / manual public-flip wording from the external case study docs.

## 0.4.0 - 2026-06-11

### Added

- Reviewer surface release: European Dimension, rerun examples, software-dev
  card, external R&D case study page, sustainability plan.
- `CLAIMBOUND-SOFTWARE_DEV_D001-2026-06-11` validated software-development card.
- `docs/case_studies/SOFTWARE_RND_EVIDENCE_CASE_STUDY.md` for external NO-GO R&D
  narrative (private staging repo until public flip).
- `docs/SUSTAINABILITY.md` maintenance and scope boundaries.

### Changed

- README foreground: three primary workflows plus future applications tier.
- Registry: 18 validated cards.

## 0.3.3 - 2026-06-11

### Added

- Added `docs/EUROPEAN_DIMENSION.md` for the European public-data and digital
  commons framing.
- Added `examples/rerun/README.md` with copy-paste local verification commands.

### Changed

- Linked European Dimension from README and reviewer summary.
- Independent rerun workflow now points to runnable example commands.

## 0.3.2 - 2026-06-11

### Added

- Added `docs/future_applications/` guides for robotics, procurement/civic and
  education/open-science secondary domains.
- Added `docs/artifacts/README.md` catalog for NYC TLC Phase 4 and CDC mirror
  artifact-only records.

### Changed

- README foreground now highlights three primary workflows: AI transparency,
  European/public open data and software development evidence.
- Evidence card README now includes card versus artifact versus scaffold table.
- Synchronized `pyproject.toml` version with release badge `v0.3.2`.

## 0.3.1 - 2026-06-05

### Added

- Added post-submit public hardening docs: reviewer summary, public roadmap
  2026, external operator starter pack, governance, maintainer boundary and
  release process.
- Added source-drift and card-boundary issue templates and external-operator
  labels/issues.

### Changed

- Clarified evidence cards versus non-card artifacts for NYC TLC and CDC mirror
  records.
- Updated release metadata from `v0.3.0` to `v0.3.1`.

### Added

- Added ClaimBound protocol v3 as a compatible tree overlay using `protocol_version: "claimbound-tree-v3"`.
- Added `iron_claim`, `flow_claim`, `tombstone`, `claimbound-tree-v3`, badge counts and branch-blocking validation rules.
- Added `src/claimbound_evidence/tree_overlay.py` for deterministic v3 tree overlay validation.
- Added CLI command `claimbound validate-tree` for `docs/track_families/*_TREE.json` overlays.
- Extended `claimbound validate-all` so optional v3 tree overlays are validated when present.
- Added script entrypoint `scripts/claimbound_validate_family_tree.py`.
- Added protocol documentation in `docs/PROTOCOL_V3_TREE_OVERLAY.md`.
- Added software developers and maintainers as a public audience category in README-facing documentation.
- Added `docs/PROTOCOL_LAYERS_V2_V3.md` to explain the difference between evidence cards, v2 family/frontier ledgers and v3 tree overlays.
- Added a software developers and maintainers scenario to `docs/AUDIENCE_TESTIMONIAL_WORKFLOWS.md`.
- Added `docs/PROTOCOL_USE_BY_LAYER_AND_AUDIENCE.md` with practical guidance for choosing card-only, v2 and v3 stacks by audience.
- Added `docs/AI_RISK_CONTROL_WITH_CLAIMBOUND.md` with practical guidance for using ClaimBound as an evidence-bound AI risk-control layer without claiming certification, runtime safety or complete risk removal.
- Added a README `ClaimBound In 30 Seconds` overview, a standalone `docs/CLAIMBOUND_IN_30_SECONDS.md` guide and a program eligibility self-check runbook.
- Added `PROGRAM_FIT_D001` as a completed non-branded program-eligibility self-check card with explicit single-operator and no-endorsement boundaries.

### Changed

- Replaced README badges that depended on dynamic GitHub-backed shields endpoints with local static SVG badges.

### Compatibility

- Historical evidence cards are not migrated or reinterpreted.
- Existing `claimbound-rnd-family-v2` family and frontier ledgers remain supported.
- v3 tree overlays are optional planning/preflight metadata; they are not result evidence by themselves.
