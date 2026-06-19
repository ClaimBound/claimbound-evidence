# Static Registry MVP Acceptance Criteria

Status: **design document only — not shipped.** See
[Planned work not shipped](PLANNED_NOT_SHIPPED.md).

## MVP scope

- Read-only generated registry views from docs/registry/evidence_index.json.
- Filters: result_status, official_source_name, domain, audience, reproduction_level.
- Links to card JSON and SVG for every entry.
- No raw payload storage in registry views.

## Required index entry fields

Mirror docs/registry/evidence_index.json cards[]:
evidence_id, path, registry_sequence, record_type, result_status, domain,
official_source_name, reproduction_level, sanitized_report_path, share_url, svg_url.

## Validation acceptance

- uv run claimbound validate-all passes.
- Every registry entry path resolves to a valid evidence card JSON.

## Non-goals

- No hosted accounts.
- No authenticated write API.
- No operator reputation system.
- No database requirement for MVP.

## Future generator

scripts/claimbound_build_registry_view.py -> docs/registry/views/
