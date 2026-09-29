# Command Reference

Generated from the CLI definitions by `scripts/gen_cli_reference.py`. Do not edit by hand.

Commands marked **needs a clone** use cards, registry or scripts that are not part of the
pip package; from a pip install they print how to clone the repository and exit with code 2.
All other commands work after `pip install claimbound-evidence`.

Global option: `--version` prints the installed version.

## `claimbound new (alias: new-track)`

Create a draft track scaffold. Prompts interactively when run in a terminal.

- `--source-url SOURCE_URL`
- `--protocol-id PROTOCOL_ID`
- `--domain DOMAIN`
- `--track-type TRACK_TYPE`
- `--execution-mode EXECUTION_MODE` (choices: `MANUAL_NO_AI`, `AUTOMATED_AI_ASSISTED`; default: `MANUAL_NO_AI`)
- `--out OUT`
- `--source-name SOURCE_NAME` (default: `Public source under review`)
- `--audience AUDIENCE` (default: `public evidence operators`)

## `claimbound demo`

**Needs a clone** of the repository.

Run a small public demo helper.

- `name` (one of: `grok-source-audit`, `eea-source-audit`, `eea-manual-probe`, `validate-all`)
- `--report REPORT`
- `--demo-root DEMO_ROOT` — Local-only root for demo source clones and reports. (default: `~/claimbound_runs/claimbound_demo`)
- `--grok-repo-dir GROK_REPO_DIR` — Existing local clone for xai-org/grok-prompts. Defaults to a local-only demo clone.

## `claimbound validate-all`

**Needs a clone** of the repository.

Validate all public evidence cards and the registry.

- `--cards-dir CARDS_DIR` (default: `docs/evidence_cards`)
- `--registry REGISTRY` (default: `docs/registry/evidence_index.json`)
- `--families-dir FAMILIES_DIR` — Directory containing optional *_FAMILY_LEDGER.json files. (default: `docs/track_families`)
- `--frontiers-dir FRONTIERS_DIR` — Directory containing optional *_FRONTIER.json files. (default: `docs/track_families`)
- `--trees-dir TREES_DIR` — Directory containing optional protocol v3 *_TREE.json files. (default: `docs/track_families`)

## `claimbound validate-family`

Validate one R&D family ledger JSON file.

- `path`

## `claimbound validate-frontier`

Validate one R&D family frontier JSON file.

- `path`
- `--base-dir BASE_DIR` — Optional base directory for context capsule and tombstone path checks.

## `claimbound validate-tree`

Validate one protocol v3 R&D tree overlay JSON file.

- `path`

## `claimbound run-root`

Create a local-only run root with standard raw/log/hash/report folders.

- `--protocol-id PROTOCOL_ID` (required)
- `--source-url SOURCE_URL` (required)
- `--operator OPERATOR` (default: `local operator`)
- `--root ROOT` — Local-only parent directory. Defaults to ~/claimbound_runs. (default: `~/claimbound_runs`)

## `claimbound doctor`

Check Python, git and repo layout for cross-platform workflows.

## `claimbound inspect`

Print selected JSON fields from cards, registry or artifacts.

### `claimbound inspect card`

- `path`
- `--keys KEYS` — Top-level JSON keys to print (default: a short card summary). (one or more values; default: `evidence_id, record_type, result_status, reproduction_level, verification_level, protocol_id, official_source_url, access_date, claim_boundary`)

### `claimbound inspect registry`

- `--registry REGISTRY` (default: `docs/registry/evidence_index.json`)
- `--keys KEYS` (one or more values; default: `registry_name, card_count`)

### `claimbound inspect json`

- `path`
- `--keys KEYS` (required; one or more values)

## `claimbound hash`

Print SHA-256 hashes for local files.

- `paths` (one or more values)
- `--out OUT` — Optional file to write hash lines.

## `claimbound validate-card`

Validate one evidence card JSON file.

- `path`

## `claimbound rerun`

**Needs a clone** of the repository.

Run frozen public-data reruns with cross-platform commands.

### `claimbound rerun nasa-d103`

- `--operator OPERATOR` (default: `local operator`)
- `--root ROOT` (default: `~/claimbound_runs`)
- `--run-dir RUN_DIR`
- `--baseline BASELINE`

### `claimbound rerun noaa-d131`

- `--operator OPERATOR` (default: `local operator`)
- `--root ROOT` (default: `~/claimbound_runs`)
- `--run-dir RUN_DIR`
- `--baseline BASELINE`

## `claimbound drift`

**Needs a clone** of the repository.

Compare fresh public-source probes against frozen baselines.

### `claimbound drift eea-source-audit`

- `--baseline BASELINE`
- `--report REPORT`

## `claimbound verify`

**Needs a clone** of the repository.

Run VERIFY pack checklists with PASS/FAIL output.

- `pack` (one of: `ai-boundary`, `api-parity`, `eea-drift`, `nasa-rerun`, `noaa-rerun`, `source-probe-spec`, `starter-pack`, `static-registry-spec`)
- `--operator OPERATOR` — Operator handle for network rerun verify packs. (default: `verify-operator`)
