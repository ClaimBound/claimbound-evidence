# Start Without Coding

This page is for reviewers, journalists and external operators who are not
software developers. You only need Python 3.12+, git and a terminal.

See [platform support](PLATFORM_SUPPORT.md) for Windows, macOS and Linux notes.

## 15-minute path

### 1. Install

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound doctor
```

`doctor` should print `ready=yes`.

### 2. Confirm the public baseline

```bash
uv run claimbound validate-all
```

Expected: `valid_cards=33` and exit code `0`.

### 3. Run one demo

```bash
uv run claimbound demo eea-source-audit
```

This writes a sanitized report under your home `claimbound_runs/` folder. A demo
is not evidence by itself.

### 4. Inspect three flagship cards

```bash
uv run claimbound inspect card docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json \
  --keys evidence_id result_status reproduction_level claim_boundary
```

Green gate pass with yellow reproduction chip means: the narrow gate passed, but
source bytes changed on rerun — not a failed gate.

### 5. Prepare a draft scaffold (optional)

Interactive:

```bash
uv run claimbound new
```

The scaffold is gray draft material until a human freezes the protocol and a
validator-checked card is published.

## One command per goal

| Goal | Command |
| --- | --- |
| Check your machine | `uv run claimbound doctor` |
| Validate all cards | `uv run claimbound validate-all` |
| Read one card field | `uv run claimbound inspect card <path> --keys ...` |
| Create draft files | `uv run claimbound new` |
| Local run folder | `uv run claimbound run-root --protocol-id ... --source-url ... --operator ...` |
| NASA rerun | `uv run claimbound rerun nasa-d103 --operator <handle>` |
| NOAA rerun | `uv run claimbound rerun noaa-d131 --operator <handle>` |
| EEA drift check | `uv run claimbound drift eea-source-audit` |
| Close VERIFY Tier A packs | `uv run claimbound verify starter-pack` (and related `verify` commands) |
| EEA drift VERIFY (#88) | `uv run claimbound verify eea-drift` |
| NASA rerun VERIFY (#86) | `uv run claimbound verify nasa-rerun --operator <handle>` |
| NOAA rerun VERIFY (#87) | `uv run claimbound verify noaa-rerun --operator <handle>` |

## What stays outside the repository

Keep raw downloads, prompt text and private notes in your local run folder only.
Publish sanitized summaries, hashes and evidence cards.

## Read next

- [ClaimBound in 30 seconds](CLAIMBOUND_IN_30_SECONDS.md)
- [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md)
- [External verification packs](external_verification/README.md)
