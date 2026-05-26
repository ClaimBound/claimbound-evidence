# Changelog

## 0.4.0 - Unreleased

### Added

- Added ClaimBound protocol v3 as a compatible tree overlay using `protocol_version: "claimbound-tree-v3"`.
- Added `iron_claim`, `flow_claim`, `tombstone`, `claimbound-tree-v3`, badge counts and branch-blocking validation rules.
- Added `src/claimbound_evidence/tree_overlay.py` for deterministic v3 tree overlay validation.
- Added CLI command `claimbound validate-tree` for `docs/track_families/*_TREE.json` overlays.
- Extended `claimbound validate-all` so optional v3 tree overlays are validated when present.
- Added script entrypoint `scripts/claimbound_validate_family_tree.py`.
- Added protocol documentation in `docs/PROTOCOL_V3_TREE_OVERLAY.md`.

### Compatibility

- Historical evidence cards are not migrated or reinterpreted.
- Existing `claimbound-rnd-family-v2` family and frontier ledgers remain supported.
- v3 tree overlays are optional planning/preflight metadata; they are not result evidence by themselves.
