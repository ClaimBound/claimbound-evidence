# Start Without Coding

This page is for reviewers, journalists and external operators who are not
software developers. You only need Python 3.12+, git and a terminal.

See [platform support](PLATFORM_SUPPORT.md) for Windows, macOS and Linux notes.

## 15-minute path

### 1. Install

```bash
git clone https://github.com/protocolith/protocolith.git
cd protocolith
uv sync --extra dev
uv run protocolith doctor
```

`doctor` should print `ready=yes`.

### 2. Confirm the public baseline

```bash
uv run protocolith validate-all
```

Expected: `valid_cards=48` and exit code `0`.

### 3. Run one demo

```bash
uv run protocolith demo eea-source-audit
```

This writes a sanitized report under your home `protocolith_runs/` folder. A demo
is not evidence by itself.

### 4. Inspect three flagship cards

```bash
uv run protocolith inspect card docs/evidence_cards/PLITH-NASA-POWER-D103-2026-04-29.json \
  --keys evidence_id result_status reproduction_level claim_boundary
```

Green gate pass with yellow reproduction chip means: the narrow gate passed, but
source bytes changed on rerun — not a failed gate.

### 5. Prepare a draft scaffold (optional)

Interactive:

```bash
uv run protocolith new
```

The scaffold is gray draft material until a human freezes the protocol and a
validator-checked card is published.

## One command per goal

| Goal | Command |
| --- | --- |
| Check your machine | `uv run protocolith doctor` |
| Validate all cards | `uv run protocolith validate-all` |
| Read one card field | `uv run protocolith inspect card <path> --keys ...` |
| Create draft files | `uv run protocolith new` |
| Local run folder | `uv run protocolith run-root --protocol-id ... --source-url ... --operator ...` |
| NASA rerun | `uv run protocolith rerun nasa-d103 --operator <handle>` |
| NOAA rerun | `uv run protocolith rerun noaa-d131 --operator <handle>` |
| EEA drift check | `uv run protocolith drift eea-source-audit` |
| Close VERIFY Tier A packs | `uv run protocolith verify starter-pack` (and related `verify` commands) |
| EEA drift VERIFY (#88) | `uv run protocolith verify eea-drift` |
| NASA rerun VERIFY (#86) | `uv run protocolith verify nasa-rerun --operator <handle>` |
| NOAA rerun VERIFY (#87) | `uv run protocolith verify noaa-rerun --operator <handle>` |

## What stays outside the repository

Keep raw downloads, prompt text and private notes in your local run folder only.
Publish sanitized summaries, hashes and evidence cards.

## Read next

- [Protocolith in 30 seconds](PROTOCOLITH_IN_30_SECONDS.md)
- [External operator starter pack](EXTERNAL_OPERATOR_STARTER_PACK.md)
- [External verification packs](external_verification/README.md)
