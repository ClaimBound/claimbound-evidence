# ClaimBound Protocol v3 Tree Overlay

Status: additive protocol v3 overlay. This document does not migrate historical
evidence cards, change evidence-card schemas or create a new empirical result.

Protocol v3 exists to make multi-track R&D easier to audit when a project has
many related branches, repeated diagnostics, stopped paths and narrow proof
claims. It sits above the existing evidence-card protocol and above the v2
family/frontier ledgers.

## Compatibility

- Existing evidence cards remain valid under their original evidence-card rules.
- Existing `claimbound-rnd-family-v2` family ledgers remain valid.
- Existing `*_FRONTIER.json` files remain optional.
- New protocol v3 overlays use `protocol_version: "claimbound-tree-v3"`.
- New protocol v3 overlays are stored as `docs/track_families/*_TREE.json`.

The tree overlay is planning, scheduling and anti-overclaim metadata. It is not
a result card.

## Why v3 Exists

The v2 family/frontier layer made related-track planning explicit. v3 adds a
compact tree view for projects where readers need to see:

- which claims are frozen proof claims versus diagnostic or flow claims;
- which branches are runnable, blocked, stopped or closed;
- which branches are blocked by tombstones;
- how many iron claims, flow claims and tombstones exist;
- why a failed branch cannot be reused as a fresh success claim.

## Terms

| Term | Meaning |
| --- | --- |
| `iron_claim` | A narrow proof-supporting claim with a frozen gate and proof-surface hash placeholder or hash. |
| `flow_claim` | A routing, diagnostic, dependency or scheduling claim that may unlock later work but is not proof by itself. |
| `tombstone` | An append-only stop record for a failed, closed, superseded or poisoned branch. |
| `claimbound-tree-v3` | The protocol string required by v3 tree overlays. |
| Badge counts | Machine-readable counts of iron claims, flow claims and tombstones for quick review. |
| Branch block rules | Rules that prevent stopped or poisoned branches from being reused as success evidence. |

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
- remove a tombstone to rescue a failed branch;
- claim deployment readiness from source, diagnostic or proof metadata alone;
- replace tests, CI, code review or maintainer judgment in software projects.

## Practical Rule

Use v3 only when the project has enough related branches that readers need a
small machine-readable tree. For a single simple evidence card, the normal
Evidence Card protocol is enough.
