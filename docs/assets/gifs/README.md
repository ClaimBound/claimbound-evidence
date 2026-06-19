# GIF Demos For ClaimBound

This folder holds short motion demos for reviewers who will not read every
runbook. GIFs complement — they do **not** replace — evidence cards and the
static workflow SVG in the README.

## File naming and placement

| File | Audience | Shown in |
| --- | --- | --- |
| `claimbound_nondev_15min.gif` | Reviewers, journalists, non-developers | `README.md`, `docs/START_WITHOUT_CODING.md` |
| `claimbound_three_cards.gif` | Anyone skimming outcomes | `docs/REVIEWER_PATH.md`, optional README |
| `claimbound_verify_tier_c.gif` | Developers, external operators | `docs/external_verification/README.md` |

Target size: **under 5 MB** per GIF (GitHub README performance). Prefer **800–1280 px** width.

Add a static first-frame PNG with the same basename for accessibility fallback, e.g.
`claimbound_nondev_15min.png`.

## Can SuperGrok / Grok Imagine make these GIFs?

**Not as authentic terminal demos.**

- Grok **Imagine** (`image_gen` / `image_edit`) produces **static images**. It
  cannot record your real terminal, `uv run claimbound doctor` output, or
  validator exit codes faithfully.
- AI-generated “fake terminal” frames would show **wrong text, wrong hashes and
  wrong card counts** — unacceptable for an evidence project.

**Use real screen recording**, then convert to GIF.

### Recommended capture tools

| OS | Tool |
| --- | --- |
| macOS | [Kap](https://getkap.co/) or QuickTime + `ffmpeg` |
| Windows | [ScreenToGif](https://www.screentogif.com/) |
| Linux | `peek`, `kazam`, or `ffmpeg` + `x11grab` |

### Conversion (if you recorded MP4)

```bash
ffmpeg -i recording.mp4 -vf "fps=10,scale=1200:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1]paletteuse" -loop 0 claimbound_nondev_15min.gif
```

Use **10 fps** and **10–45 seconds** total length.

### When SuperGrok *is* appropriate

Only for **illustrative** non-evidence art (logo motion, abstract workflow) — not
for commands, hashes or card JSON. ClaimBound does **not** require AI illustration
GIFs for reviewer credibility.

---

## GIF 1 — Non-developer 15-minute path (required)

**Filename:** `docs/assets/gifs/claimbound_nondev_15min.gif`

**Duration:** 35–45 seconds · **no audio** · large monospace font · light terminal theme

**Exact command script** (run on a clean clone; hide username paths if visible):

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json --keys evidence_id result_status claim_boundary reproduction_level
```

Then **pause 3 seconds** on the inspect output. Optionally open the matching SVG in a
browser tab (file URL or GitHub raw view) for 5 seconds.

**On-screen captions** (burn in or overlay subtitles):

1. `Install + doctor`
2. `24 validated cards`
3. `Inspect one EU card — narrow claim only`

**Must show on screen:** `ready=yes`, `valid_cards=24`, exit code `0`.

**Must NOT show:** private paths, API keys, private application text, edited card JSON.

---

## GIF 2 — Three outcome types (optional, high value)

**Filename:** `docs/assets/gifs/claimbound_three_cards.gif`

**Duration:** 20–25 seconds · no terminal required

**Content:** slow crossfade or horizontal scroll of three **committed SVG** files
(open locally or on GitHub):

1. `docs/evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg` — green
2. `docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg` — green + yellow reproduction chip
3. `docs/evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg` — red negative

**Caption sequence:**

1. `Green = narrow pass`
2. `Yellow chip = source-byte drift, not failed gate`
3. `Red = honest negative — still evidence`

**SuperGrok prompt (only if you lack screen recording):** do **not** use for this GIF.
Record browser scrolling real SVGs instead.

---

## GIF 3 — Developer verify pack (optional)

**Filename:** `docs/assets/gifs/claimbound_verify_tier_c.gif`

**Duration:** 60–90 seconds · macOS or Windows terminal

**Command script:**

```bash
uv run claimbound doctor
uv run claimbound verify starter-pack
# optional tail of NASA pack:
uv run claimbound verify nasa-rerun --operator YOUR_GITHUB_HANDLE
```

**Captions:** `Baseline` → `Tier A verify` → `Tier C rerun (external operator)`

Replace `YOUR_GITHUB_HANDLE` with the real external operator handle when recording
for VERIFY closure — not `maintainer`.

---

## How to insert GIFs into the open-source project

### 1. Add files

```bash
# from repository root
cp ~/Downloads/claimbound_nondev_15min.gif docs/assets/gifs/
cp ~/Downloads/claimbound_nondev_15min.png docs/assets/gifs/   # optional fallback
```

### 2. Embed in README.md

Place after the workflow SVG block:

```markdown
### Quick demo (non-developer)

![15-minute ClaimBound baseline demo](docs/assets/gifs/claimbound_nondev_15min.gif)

No terminal? See [Start without coding](docs/START_WITHOUT_CODING.md).
```

### 3. Embed in START_WITHOUT_CODING.md

After the “15-minute path” heading:

```markdown
![15-minute baseline demo](../assets/gifs/claimbound_nondev_15min.gif)
```

### 4. Embed in REVIEWER_PATH.md

In the “Visual walkthrough” section:

```markdown
![Three flagship outcome types](assets/gifs/claimbound_three_cards.gif)
```

### 5. Commit and PR

```bash
git add docs/assets/gifs/
git add README.md docs/START_WITHOUT_CODING.md docs/REVIEWER_PATH.md
git commit -m "docs: add reviewer GIF demos"
```

Run before PR:

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

### 6. Accessibility

- Keep alt text descriptive (see examples above).
- Do not autoplay sound.
- Prefer GIF under 5 MB; use MP4 in `docs/assets/gifs/` only if GitHub LFS or
  release assets are used — GIF in README is simpler for reviewers.

---

## Maintainer checklist before merging GIFs

- [ ] Card count in recording matches current `validate-all` (24).
- [ ] Test count matches current pytest (86).
- [ ] No private paths, tokens or private application text visible.
- [ ] Green / red / yellow semantics match [Common misreadings](../../COMMON_MISREADINGS.md).
- [ ] GIFs are real recordings or real SVG scroll — not AI-invented terminals.