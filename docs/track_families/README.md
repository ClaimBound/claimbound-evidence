# Track Family Ledgers

This directory is for R&D family ledgers, optional frontier ledgers and optional
protocol v3 tree overlays created by `uv run claimbound new` or by future family
orchestration tools.

A family ledger is not evidence. It is planning and preflight metadata for one
track or many related tracks: parent claim, non-overlap boundary, claim list,
track modes, proof surface, proof-track budget, stop rules and closure
decisions.

A frontier ledger is also not evidence. It is a compact machine-readable view of
alive, stopped and closed work. In a one-track workflow it can stay small; in a
larger workflow it can coordinate families, consumed tombstones and blocked
proof surfaces.

A protocol v3 tree overlay is also not evidence. It is a compact tree view for
one track or many related tracks: iron claims, flow claims, tombstones, badge
counts and branch-blocking rules. It uses `protocol_version:
"claimbound-tree-v3"` and is stored as `*_TREE.json`.

Validate a ledger before citing track state:

```bash
uv run claimbound validate-family docs/track_families/<ID>_FAMILY_LEDGER.json
```

or:

```bash
uv run python scripts/claimbound_validate_family_ledger.py \
  docs/track_families/<ID>_FAMILY_LEDGER.json
```

Validate a frontier:

```bash
uv run claimbound validate-frontier docs/track_families/<ID>_FRONTIER.json
```

or:

```bash
uv run python scripts/claimbound_validate_family_frontier.py \
  docs/track_families/<ID>_FRONTIER.json
```

Validate a v3 tree overlay:

```bash
uv run claimbound validate-tree docs/track_families/<ID>_TREE.json
```

or:

```bash
uv run python scripts/claimbound_validate_family_tree.py \
  docs/track_families/<ID>_TREE.json
```

Validated evidence still lives in `docs/evidence_cards/`. The ledger prevents
diagnostic screening, repeated proof attempts or closed branches from being
misread as a completed evidence result.

Historical evidence cards created before these protocols do not need
retroactive ledgers or tree overlays. New ledgers and overlays are optional
planning records and are validated only when a matching `*_FAMILY_LEDGER.json`,
`*_FRONTIER.json` or `*_TREE.json` file exists.

## Current Example Set

| File | Role |
| --- | --- |
| [PROGRAM_FIT_D001_FAMILY_LEDGER.json](PROGRAM_FIT_D001_FAMILY_LEDGER.json) | v2 family contract for the program-fit self-check track. |
| [PROGRAM_FIT_D001_FRONTIER.json](PROGRAM_FIT_D001_FRONTIER.json) | v2 frontier state: primary track closed after the evidence card was published. |
| [PROGRAM_FIT_D001_TREE.json](PROGRAM_FIT_D001_TREE.json) | v3 tree overlay for the same family. |
