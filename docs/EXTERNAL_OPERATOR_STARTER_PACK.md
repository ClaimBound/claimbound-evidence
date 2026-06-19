# External Operator Starter Pack

Use this page when you want to try ClaimBound from outside the project. You do
not need private data, private technology or a hosted account.

## Choose One Path

| Path | Use when | Start here |
| --- | --- | --- |
| Close VERIFY issues | You were asked to verify maintainer deliverables (#85–#87). | [External verification packs](external_verification/README.md) — ~15 min first time, ~5 min per pack after setup |
| Read existing evidence | You want to understand what ClaimBound cards prove. | [Evidence cards](evidence_cards/README.md) |
| Request a new card | You have one narrow public claim that should be checked. | Open an `Evidence request` issue. |
| Rerun an existing card | You want to reproduce or challenge a published card. | Open a `Reproduction request` issue. |
| Report source drift | A public source changed after a card was published. | Open a `Source drift report` issue. |
| Ask about boundaries | You think a card proves too much or too little. | Open a `Card boundary question` issue. |

## Minimal Local Setup

Works on Windows, macOS and Linux. Prerequisites: Python 3.12+, git. See
[platform support](PLATFORM_SUPPORT.md).

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

If `uv run claimbound validate-all` passes, the committed cards and registry are
valid under the current validators.

## Try A Local Scaffold

A scaffold is not evidence. It prepares the files an operator would review
before freezing a real protocol.

```bash
uv run claimbound new \
  --source-url "https://example.org/source-docs" \
  --protocol-id "EXAMPLE_D001" \
  --domain "public-data" \
  --track-type "source_audit" \
  --execution-mode "MANUAL_NO_AI" \
  --out "claimbound_runs/EXAMPLE_D001/scaffold"
```

Keep raw payloads, transcripts and restricted source materials outside this
repository.

## Rerun An Existing Card

1. Pick a card from [docs/evidence_cards](evidence_cards/README.md).
2. Read the original protocol or playbook before collecting fresh outcomes.
3. Create a local run root:

```bash
uv run claimbound run-root \
  --protocol-id "NASA_POWER_D103" \
  --source-url "https://power.larc.nasa.gov/docs/services/api/temporal/daily/" \
  --operator "your-name-or-handle"
```

4. Record source access date, source URL, command and environment notes.
5. Keep raw payloads outside this repository.
6. Publish only sanitized summaries, hashes, limitations and evidence cards.
7. Use the reproduction PR template.

See [Independent rerun workflow](INDEPENDENT_RERUN_WORKFLOW.md).

## What Not To Claim

ClaimBound cards are deliberately narrow. A card must not be used to claim:

- model safety or deployment readiness from a source audit;
- broad model superiority from a small benchmark;
- legal, procurement or award approval;
- investment advice or production forecasting quality;
- raw-byte reproduction when source bytes changed;
- endorsement by a source owner or program sponsor.

## Planned Work Versus Shipped Baseline

SourceProbe v1, static registry views, PyPI and a WCAG pass are roadmap items.
They are **not** claimed as shipped. See [Planned work not shipped](PLANNED_NOT_SHIPPED.md).

NYC TLC Phase 4 and CDC mirror summaries are [artifact-only records](artifacts/README.md),
not registry cards.

## Good First Issues To Open

Open an issue when you can provide one of these:

- a narrow public claim with a source URL;
- a source drift observation for a committed card;
- a rerun request for an existing card;
- a boundary question about what a card proves;
- a developer example such as API parity, CI/regression evidence or an
  AI-assisted code-change evidence trail.

Do not post credentials, API keys, raw private data, private transcripts,
personal data or private reviewer communication in public issues.

