# ClaimBound Protocol v3 Tree Overlay

Status: additive protocol v3 overlay. This document does not migrate historical
evidence cards, change evidence-card schemas or create a new empirical result.

Protocol v3 is a universal tree overlay. It can describe one track with one node
or many related branches with many nodes. It sits above the existing
evidence-card protocol and above the v2 family/frontier ledgers.

## Compatibility

- Existing evidence cards remain valid under their original evidence-card rules.
- Existing `claimbound-rnd-family-v2` family ledgers remain valid.
- Existing `*_FRONTIER.json` files remain optional.
- New protocol v3 overlays use `protocol_version: "claimbound-tree-v3"`.
- New protocol v3 overlays are stored as `docs/track_families/*_TREE.json`.

The tree overlay is planning, scheduling and anti-overclaim metadata. It is not
a result card.

## How The Layers Fit

ClaimBound keeps three protocol layers separate and universal:

| Layer | One-track use | Multi-track use |
| --- | --- | --- |
| Evidence card protocol | Record one completed result, status, boundary and rerun path. | Record each completed evidence leaf without changing the card schema. |
| Family/frontier protocol v2 | Keep one claim list, proof surface, stop rule and closure boundary. | Coordinate budgets, frontiers, tombstones and closure across related tracks. |
| Tree overlay v3 | Publish a one-node status map with optional iron, flow and tombstone references. | Publish a larger tree of evidence leaves, reusable bounded claims, volatile gates and stopped branches. |

A one-track overlay is not a weaker or special-case protocol. It is the same
`claimbound-tree-v3` structure with one node and small counts.

## Why v3 Exists

The v2 family/frontier layer made planning explicit. v3 adds a compact tree view
for projects where readers need to see:

- which claims are frozen proof claims versus diagnostic or flow claims;
- which work is runnable, blocked, stopped or closed;
- which branches are blocked by tombstones;
- how many iron claims, flow claims and tombstones exist;
- why a failed branch cannot be reused as a fresh success claim.

For a single track, the same fields make the result boundary easier to inspect.
For many tracks, they prevent repeated diagnostics, stale dependencies and
stopped paths from being confused with proof.

## Terms

| Term | Meaning |
| --- | --- |
| `iron_claim` | A narrow bounded claim with stable evidence and proof-surface hash placeholder or hash. |
| `flow_claim` | A volatile routing, dependency, availability or scheduling claim that may unlock later work but is not proof by itself. |
| `tombstone` | An append-only stop record for a failed, closed, superseded or poisoned branch. |
| `claimbound-tree-v3` | The protocol string required by v3 tree overlays. |
| Badge counts | Machine-readable counts of iron claims, flow claims and tombstones for quick review. |
| Branch block rules | Rules that prevent stopped or poisoned work from being reused as success evidence. |

## Minimum Tree Overlay

```json
{
  "tree_id": "EXAMPLE_D001_TREE",
  "protocol_version": "claimbound-tree-v3",
  "tree_status": "ACTIVE",
  "root_family_id": "EXAMPLE_D001_FAMILY",
  "claim_nodes": [
    {
      "claim_id": "EXAMPLE_D001-C001",
      "claim_kind": "iron_claim",
      "status": "FROZEN",
      "claim_text": "The frozen source boundary is identified before outcome scoring.",
      "evidence_required": ["source URL", "access date", "rights note"],
      "acceptance_gate": "Source boundary is recorded before the proof track runs.",
      "forbidden_inference": ["source availability alone is not proof of the empirical claim"],
      "proof_surface_hash": "NOT_COMPUTED_UNTIL_FREEZE"
    },
    {
      "claim_id": "EXAMPLE_D001-C002",
      "claim_kind": "flow_claim",
      "status": "DRAFT",
      "claim_text": "A later diagnostic track may inspect source coverage without proof status.",
      "evidence_required": ["diagnostic summary", "no-proof boundary"],
      "acceptance_gate": "Diagnostic output is recorded only as candidate or blocker evidence.",
      "forbidden_inference": ["diagnostic output is not a deployment or production claim"]
    }
  ],
  "track_nodes": [
    {
      "track_id": "EXAMPLE_D001-T001",
      "mode": "source_audit",
      "claim_ids": ["EXAMPLE_D001-C001"],
      "dependencies": [],
      "branch_status": "runnable"
    }
  ],
  "tombstones": [],
  "badge_counts": {
    "iron_claims": 1,
    "flow_claims": 1,
    "tombstones": 0
  },
  "branch_block_rules": [
    "A stopped branch must publish a tombstone before descendants can be treated as runnable."
  ]
}
```

## Validation

Validate one v3 tree overlay:

```bash
uv run claimbound validate-tree docs/track_families/EXAMPLE_D001_TREE.json
```

Equivalent script entrypoint:

```bash
uv run python scripts/claimbound_validate_family_tree.py \
  docs/track_families/EXAMPLE_D001_TREE.json
```

Validate all public evidence cards, the registry, optional v2 family/frontier
ledgers and optional v3 tree overlays:

```bash
uv run claimbound validate-all
```

## What v3 Must Not Do

A v3 tree overlay must not:

- reinterpret an old card as stronger evidence;
- turn a diagnostic claim into proof;
- promote a stale flow claim into an iron claim;
- remove a tombstone to rescue a failed branch;
- claim deployment readiness from source, diagnostic or proof metadata alone;
- replace tests, CI, code review or maintainer judgment in software projects.

## Practical Rule

Use v3 when you want a public status map for a track. Keep it one-node and
small for a single track. Expand it only when related tracks, flow dependencies,
iron claims or tombstones make that useful.
