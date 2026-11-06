# Accessibility of evidence-card SVGs

This page describes the accessibility checks the repository runs on its
evidence-card SVGs and, just as importantly, what it does not claim.

## What the renderer emits

`claimbound_evidence.card_svg_render` writes each card with:

- `role="img"` on the root `<svg>`;
- `aria-labelledby="cb-title cb-desc"` pointing at a `<title>` (card name and
  evidence ID) and a `<desc>` (result status, reproduction level, the allowed
  narrow claim and the claim boundary);
- text and background colours whose contrast ratio is at least 4.5:1. The
  status-chip gradients (white text) were darkened to satisfy this; the
  ratio is computed with the WCAG 2.x relative-luminance formula in
  `claimbound_evidence.card_svg_styles.contrast_ratio`.

## What the linter checks

`claimbound_evidence.svg_a11y.lint_svg_text` and
`scripts/claimbound_lint_svg_a11y.py` check every SVG under `docs/` for:

1. well-formed XML with an `<svg>` root;
2. `role="img"`;
3. `aria-labelledby` resolving to a non-empty `<title>` and `<desc>`;
4. text `fill` colours with at least 4.5:1 contrast against the card page
   backgrounds, and white chip text against every colour stop of the status
   gradients used in the file.

```bash
uv run python scripts/claimbound_lint_svg_a11y.py           # counts only
uv run python scripts/claimbound_lint_svg_a11y.py --list    # per-file findings
uv run python scripts/claimbound_lint_svg_a11y.py --strict  # exit 1 on findings
```

The default mode is report-only. Existing SVGs are historical output of earlier
renderer versions; they were not edited by hand and are reported, not rewritten.
Re-rendering them is an explicit, separate step
(`scripts/claimbound_render_evidence_card_svg.py`).

## Not claimed

- No WCAG conformance level (A, AA or AAA) is claimed and no third-party
  accessibility audit has been performed.
- Only colour contrast of declared text fills and the presence of a text
  alternative are checked. Reading order, text resizing, zoom, forced-colours
  mode, keyboard use and assistive-technology testing are not evaluated.
- The decorative ClaimBound logotype is not contrast-checked.
- The linter reads declared `fill` attributes; text whose colour is set by CSS
  or inherited is not analysed.
- Rendered cards are images: the long text they contain is summarised in
  `<desc>`; the full record is the JSON card.

## Related non-breaking card checks

`claimbound_evidence.evidence_card.warn_evidence_card` adds warnings (SHA-256
format, ISO-8601 dates, claim-boundary length, limitation list shape, source
URL scheme). They never fail validation; `scripts/claimbound_validate_registry.py`
prints their counts to stderr (`--show-warnings` lists each one).
