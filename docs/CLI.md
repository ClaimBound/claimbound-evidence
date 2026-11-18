# Command Reference

Generated from the CLI definitions by `scripts/gen_cli_reference.py`. Do not edit by hand.

Commands marked **needs a clone** use cards, registry or scripts that are not part of the
pip package; from a pip install they print how to clone the repository and exit with code 2.
All other commands work after `pip install protocolith`.

Global option: `--version` prints the installed version.

## `protocolith new (alias: new-track)`

Create a draft track scaffold. Prompts interactively when run in a terminal.

- `--source-url SOURCE_URL`
- `--protocol-id PROTOCOL_ID`
- `--domain DOMAIN`
- `--track-type TRACK_TYPE`
- `--execution-mode EXECUTION_MODE` (choices: `MANUAL_NO_AI`, `AUTOMATED_AI_ASSISTED`; default: `MANUAL_NO_AI`)
- `--out OUT`
- `--source-name SOURCE_NAME` (default: `Public source under review`)
- `--audience AUDIENCE` (default: `public evidence operators`)
- `--dry-run` — List the files that would be created and write nothing.

## `protocolith demo`

**Needs a clone** of the repository.

Run a small public demo helper.

- `name` (one of: `grok-source-audit`, `eea-source-audit`, `eea-manual-probe`, `validate-all`)
- `--report REPORT`
- `--demo-root DEMO_ROOT` — Local-only root for demo source clones and reports. (default: `~/protocolith_runs/protocolith_demo`)
- `--grok-repo-dir GROK_REPO_DIR` — Existing local clone for xai-org/grok-prompts. Defaults to a local-only demo clone.

## `protocolith validate-all`

**Needs a clone** of the repository.

Validate all public evidence cards and the registry.

- `--cards-dir CARDS_DIR` (default: `docs/evidence_cards`)
- `--registry REGISTRY` (default: `docs/registry/evidence_index.json`)
- `--families-dir FAMILIES_DIR` — Directory containing optional *_FAMILY_LEDGER.json files. (default: `docs/track_families`)
- `--frontiers-dir FRONTIERS_DIR` — Directory containing optional *_FRONTIER.json files. (default: `docs/track_families`)
- `--trees-dir TREES_DIR` — Directory containing optional protocol v3 *_TREE.json files. (default: `docs/track_families`)

## `protocolith validate-family`

Validate one R&D family ledger JSON file.

- `path`

## `protocolith validate-frontier`

Validate one R&D family frontier JSON file.

- `path`
- `--base-dir BASE_DIR` — Optional base directory for context capsule and tombstone path checks.

## `protocolith validate-tree`

Validate one protocol v3 R&D tree overlay JSON file.

- `path`

## `protocolith run-root`

Create a local-only run root with standard raw/log/hash/report folders.

- `--protocol-id PROTOCOL_ID`
- `--source-url SOURCE_URL`
- `--operator OPERATOR` (default: `local operator`)
- `--root ROOT` — Local-only parent directory. Defaults to ~/protocolith_runs. (default: `~/protocolith_runs`)

### `protocolith run-root deviation`

#### `protocolith run-root deviation add`

- `--run-dir RUN_DIR` (required)
- `--step STEP` (required)
- `--planned PLANNED` (required)
- `--happened HAPPENED` (required)
- `--reason REASON` (required)
- `--who WHO` (required)

#### `protocolith run-root deviation list`

- `--run-dir RUN_DIR` (required)

### `protocolith run-root rights`

#### `protocolith run-root rights answer`

- `--run-dir RUN_DIR` (required)
- `--question-id QUESTION_ID` (required)
- `--answer ANSWER` (required)
- `--who WHO` (required)

## `protocolith doctor`

Check Python, git and repo layout for cross-platform workflows.

## `protocolith inspect`

Print selected JSON fields from cards, registry or artifacts.

### `protocolith inspect card`

- `path`
- `--keys KEYS` — Top-level JSON keys to print (default: a short card summary). (one or more values; default: `evidence_id, record_type, result_status, reproduction_level, verification_level, protocol_id, official_source_url, access_date, claim_boundary`)

### `protocolith inspect registry`

- `--registry REGISTRY` (default: `docs/registry/evidence_index.json`)
- `--keys KEYS` (one or more values; default: `registry_name, card_count`)

### `protocolith inspect json`

- `path`
- `--keys KEYS` (required; one or more values)

## `protocolith hash`

Print SHA-256 hashes for local files.

- `paths` (one or more values)
- `--out OUT` — Optional file to write hash lines.

## `protocolith validate-card`

Validate one evidence card JSON file.

- `path`

## `protocolith rerun`

**Needs a clone** of the repository.

Run frozen public-data reruns with cross-platform commands.

### `protocolith rerun nasa-d103`

- `--operator OPERATOR` (default: `local operator`)
- `--root ROOT` (default: `~/protocolith_runs`)
- `--run-dir RUN_DIR`
- `--baseline BASELINE`

### `protocolith rerun noaa-d131`

- `--operator OPERATOR` (default: `local operator`)
- `--root ROOT` (default: `~/protocolith_runs`)
- `--run-dir RUN_DIR`
- `--baseline BASELINE`

### `protocolith rerun report`

Compare original vs rerun hashes; never modifies a card or claim.

- `--original ORIGINAL` (required)
- `--rerun RERUN` (required)
- `--outcome OUTCOME` (choices: `matches`, `differs`, `unknown`; default: `unknown`)
- `--blocked`
- `--note NOTE` (default: ``)
- `--out OUT`

## `protocolith drift`

**Needs a clone** of the repository.

Compare fresh public-source probes against frozen baselines.

### `protocolith drift eea-source-audit`

- `--baseline BASELINE`
- `--report REPORT`

## `protocolith probe`

SourceProbe v1: metadata-only probe of one public URL (no legal conclusion).

- `url`
- `--marker MARKER` — Case-sensitive text to look for.
- `--out OUT` — Write the JSON probe artifact here.
- `--json` — Print the JSON artifact.

## `protocolith verify`

**Needs a clone** of the repository.

Run VERIFY pack checklists with PASS/FAIL output.

- `pack` (one of: `ai-boundary`, `api-parity`, `eea-drift`, `nasa-rerun`, `noaa-rerun`, `source-probe-spec`, `starter-pack`, `static-registry-spec`)
- `--operator OPERATOR` — Operator handle for network rerun verify packs. (default: `verify-operator`)

## `protocolith freeze`

Freeze a protocol from a JSON file.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `file`
- `--supersedes SHA256` — Hash of the protocol version this replaces.

## `protocolith record`

Record a run outcome from a JSON file.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `file`

## `protocolith deviation`

Record a deviation from a JSON file.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `file`

## `protocolith verify-ledger`

Verify the ledger (rules R1 to R11).

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--expect-head SEQ:HASH` — Also require the entry at SEQ to have this hash (detects a removed tail); else HEAD_MISMATCH, exit 1.
- `--anchors` — Also check every anchor in the store: ANCHOR_MISMATCH (rewritten), ANCHOR_AHEAD (truncated), exit 1.

## `protocolith anchor`

Anchor the ledger head: a local anchor file, and optionally a time-stamp, an archive copy or a git tag.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--tsa URL` — Also get an RFC 3161 time-stamp (a network request; the signature is not verified here).
- `--wayback URL` — Ask the Wayback Machine to save URL, where you published the statement.
- `--git-tag` — Create the git tag anchor/SEQ-HASH12 in this repository (never pushed).
- `--sign` — Sign the git tag (needs --git-tag and a configured key).
- `--write-head FILE` — Write the anchor statement to FILE to publish or archive it.

## `protocolith disclose`

Write a publishable view of the ledger: each entry shown in full, as a summary, or hidden, as a policy says.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--policy FILE` — Visibility policy (`protocolith schema policy`). (required)
- `--out FILE` — Output file (default disclosure.jsonl). (default: `disclosure.jsonl`)

## `protocolith verify-disclosure`

Check the structure and hash chain of a disclosure and the hash of every full entry. --anchors DIR compares the anchor statements there with the entry hashes; --reveal FILE checks that a ledger entry you were given is exactly the one the disclosure committed to.

- `file`
- `--anchors DIR` — Directory of anchor statements (.json) to check.
- `--reveal ENTRY` — JSON file holding one revealed ledger entry.
- `--json` — Print the result as canonical JSON.

## `protocolith claim-check`

State what the ledger supports about a record (what may and may not be said).

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--seq N` — The record at ledger seq N.
- `--protocol ID` — The latest record of this protocol_id.

## `protocolith issue`

Issue the evidence card of a record.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `seq`
- `--out DIR` — Card directory (default <store>/cards).

## `protocolith log`

List ledger entries, optionally filtered.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--protocol ID` — Only entries of this protocol_id.
- `--type TYPE` — Only entries of this type. (choices: `freeze`, `record`, `deviation`, `issue`)
- `--status STATUS` — Only records with this result status. (choices: `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE`, `NEGATIVE_RESULT_UNDER_PROTOCOL`, `PASSED_UNDER_PROTOCOL`, `REPRODUCED_OUTCOME`, `SOURCE_DRIFT`)
- `--tail N` — Keep only the last N matching entries.

## `protocolith show`

Show one entry with its protocol context.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `seq`

## `protocolith summary`

Verdict, head, counts and a per-protocol table in one call.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--protocol ID` — Only this protocol_id.

## `protocolith init`

Create the store with an empty ledger (safe to repeat).

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.

## `protocolith capture`

Print a JSON fragment for the outcome object of a record: Python, platform, machine and protocolith version, and the relative path, size and sha256 of each --file (inside the current directory). Runs nothing and reads no environment values.

- `--json` — Print errors as canonical JSON.
- `--file PATH` — File to hash; repeat for several.
- `--env` — Include the environment (implied when no --file is given).

## `protocolith schema`

Print a JSON Schema (draft 2020-12) generated from the rules.

- `name` — Which schema (default all). (one of: `freeze`, `record`, `deviation`, `issue`, `entry`, `policy`, `all`)

## `protocolith head`

Print the ledger head (last hash and seq).

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.

## `protocolith repair`

Repair a crash-damaged ledger.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--truncate-partial-tail` — Remove the partial last line. (required)

## `protocolith atlas`

Build a self-contained offline HTML atlas of experiments from a ledger and/or evidence card directories.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
- `--json` — Print the result as canonical JSON.
- `--cards DIR` — Directory of evidence card JSON files, searched recursively; repeat for several. Without --store and --cards: a local ledger, else docs/evidence_cards.
- `--out FILE_OR_DIR` — Output .html file or directory (default protocolith-atlas.html). (default: `protocolith-atlas.html`)
- `--title TEXT` — Page title. (default: `Protocolith atlas`)
- `--i18n DIR` — Directory of <code>.json translation files; adds a language switcher.
- `--default-lang CODE` — Initial language (default en). (default: `en`)
- `--policy FILE` — Visibility policy: show each record in full, as a summary, or hidden.
- `--max-rows N` — Embed at most N records (the newest); counts stay complete.

## `protocolith mcp`

Run the MCP server on stdio.

- `--store STORE` — Store directory (env PROTOCOLITH_STORE, default .protocolith).
