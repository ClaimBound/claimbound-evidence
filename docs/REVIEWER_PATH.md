# Reviewer Path (One Page)

This page is for first-time readers, journalists, program reviewers and external
operators who need a fast honest picture of the public repository. It is not an
endorsement, legal opinion or private application document.

## The question ClaimBound answers

```text
Where is the evidence?
```

A public claim becomes a small **evidence card**: frozen protocol, source
boundary, exact result status, sanitized hashes, claim boundary and reproduction
level. No card means the statement is still only a claim.

## Five-minute inspection (no coding depth required)

1. Read [ClaimBound in 30 seconds](CLAIMBOUND_IN_30_SECONDS.md).
2. Skim three flagship cards in the README:
   - green source audit (Anthropic or EEA),
   - green gate with yellow reproduction chip (NASA POWER D-103),
   - red honest negative (NOAA CO-OPS D-131).
3. Run the portable baseline (Windows, macOS or Linux):

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
```

Expected: `ready=yes`, `valid_cards=33`, exit code `0`.

4. Read [Planned work not shipped](PLANNED_NOT_SHIPPED.md) — SourceProbe v1,
   static registry HTML views, PyPI and WCAG are **not** claimed as completed.

## What is already strong

| Signal | Where to look |
| --- | --- |
| Honest mixed outcomes | Green, red, amber blocked and yellow drift cards in [registry](registry/evidence_index.json) |
| European open-data angle | [European Dimension](EUROPEAN_DIMENSION.md) and five EU-related examples |
| Cross-platform operator CLI | `doctor`, `inspect`, `rerun`, `drift`, `verify` — [platform support](PLATFORM_SUPPORT.md) |
| Scope discipline | [Reviewer summary](REVIEWER_SUMMARY.md) — not OSF, not OpenML, not certification |
| Artifact honesty | [Artifacts catalog](artifacts/README.md) — NYC TLC / CDC are artifact-only, not registry cards |

## The main credibility gap (stated openly)

All **33** registry cards currently use `SINGLE_OPERATOR` or
`SINGLE_OPERATOR_RERUN`. There is **no** `INDEPENDENT_RERUN` or
`MULTI_OPERATOR` card yet.

Maintainer bootstrap runs closed VERIFY mirrors #88–#92 for repository hygiene.
**Independent external closure** of **#85, #86 or #87** is the acceptance signal.
See [External verification packs](external_verification/README.md): first setup
~15 min; each open issue closes with one `claimbound verify …` command (~2 min)
after baseline. Minimum credible signal: **#85 + one of #86/#87** from an
operator who is **not** the maintainer.

## What is planned but not shipped

See [Public roadmap 2026](ROADMAP_2026.md) and
[Planned work not shipped](PLANNED_NOT_SHIPPED.md). Acceptance-criteria documents
are specifications until implementation lands on `main`.

## Read next by role

| Role | Next page |
| --- | --- |
| Non-developer | [Start without coding](START_WITHOUT_CODING.md) |
| External operator | [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md) |
| Deeper comparison | [Reviewer summary](REVIEWER_SUMMARY.md) |
| EU public-interest framing | [European Dimension](EUROPEAN_DIMENSION.md) |
| Common mistakes | [Common misreadings](COMMON_MISREADINGS.md) |
| End-to-end EU example | [EEA source audit case study](case_studies/EEA_SOURCE_AUDIT_CASE_STUDY.md) |
