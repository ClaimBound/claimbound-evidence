Protocolith brand assets
========================

FILES (bytes)
  concept_a.svg          2108
  concept_b.svg          2306
  concept_c.svg          7011
  contact_sheet.svg      109897
  demo.gif               247755
  favicon.svg            422
  logo-dark.svg          2311
  logo-mark-512.png      4421
  logo-mark.svg          1359
  logo.svg               2312
  social-preview.png     21448
  social-preview.svg     23661
  workflow.gif           92014

All SVGs are pure vector with outlined text (no external fonts, no raster) and carry <title> and <desc>.
Wordmark "Protocolith": own monoline geometric letterforms (stroked paths, no font involved).
Tagline and contact-sheet labels: outlined from Source Sans Pro (SIL OFL 1.1, embedding outlines permitted).
Palette (chosen concept B): stone blue #1F3A5F (light) / #3E6BA8 (dark), facet #3B5E8F / #5B8AC9,
hash ticks amber #E8B04A / #F0B545, ink #17202B, light text #EEF2F6, dark ground #0E141B.
Text contrast (WCAG): ink on white 16.4:1, light text on dark 16.5:1, tagline #B4BFCB on dark 9.9:1.

CONCEPTS
  A  Monolith: faceted slab, carved dashed lines read as protocol steps, last step amber.
  B  Cut P: stone block with a P cut through it (the stone refills the counter), chamfered corner,
     a row of 12 hash-like ticks. Tick heights come from the first 12 hex digits of SHA-256("protocolith").
  C  Seal: notched rim with 60 teeth, concentric incised rings, notch at the top, carved P.
  Shipped set (logo.svg, logo-dark.svg, logo-mark.svg, favicon.svg, social-preview.*) is concept B.

RECOMMENDATION: B (Cut P)
It is the only mark that stays legible and unmistakable at 16 px (see favicon), because the letter
itself is the shape; a P cut into stone says "protocol cut in stone" directly. The hash ticks give the
technical, verifiable character without any cliche (no lock, shield or chain), and the amber accent
marks "recorded" detail. A is more literal but reads as a generic tower/server at small sizes;
C is handsome but detailed rings and teeth vanish below about 32 px.

DEMO GIF (demo.gif): real output, run in the repository root with UV_CACHE_DIR set to a temp directory
  uv run protocolith --version
  uv run protocolith doctor
  uv run protocolith inspect registry
  uv run protocolith validate-card docs/evidence_cards/PLITH-AI_PRODUCT_CLAIM_D001-2026-05-07.json
  uv run protocolith hash LICENSE
  uv run protocolith verify static-registry-spec      (works offline, rc=0, all PASS)
All six commands exited 0. Edits to the captured text, nothing else changed:
  - doctor: the two lines repo_root= and runs_root= (absolute home paths) are replaced by one
    dimmed "# ... omitted (local paths)" note.
  - hash and verify: the absolute repository prefix is shown as <repo>/.
  - The card file name in the validate-card line contains "AI" because that is the real file name.
Not run: verify packs that need network (nasa-rerun, noaa-rerun, eea-drift, api-parity, ai-boundary was
run once to check it works but is not shown). Typed-command animation 3 chars/frame at 12 fps, loops forever.

WORKFLOW GIF (workflow.gif): drawn with Pillow, 900x300, 10 fps, loops. Captioned "Workflow overview"
and "Design overview, not a product demo".

FAILED / CAVEATS
  - First attempt of the demo commands failed because of my own shell quoting (subcommand passed as one
    argument); re-run correctly, no product failure.
  - PNGs rendered with resvg-py (social-preview.png 1280x640, logo-mark-512.png 512x512): worked.
  - Final README references and repository wiring were not touched (write scope limited to this folder).
