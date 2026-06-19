# SourceProbe v1 Acceptance Criteria

Status: **design document only — not shipped.** This is not an implementation or
evidence record. See [Planned work not shipped](PLANNED_NOT_SHIPPED.md).

## Purpose

Define acceptance criteria for SourceProbe v1 before implementation.

## Required JSON fields

- http_status
- final_url
- content_type
- byte_size
- sha256 (when safe to hash)
- expected_marker_checks
- license_or_terms_links (hints only)
- recommendation: safe_to_continue | needs_human_review | blocked
- no_legal_conclusion: true

## Non-goals

- Must not emit PASSED_UNDER_PROTOCOL by itself.
- Must not make legal reuse conclusions.
- Must not replace human-reviewed protocol or card boundary.

## Valid example reference

See artifacts/source_audit_d001_source_probe_summary.json (scaffold only).

## Invalid examples

- Probe output claiming model safety or deployment readiness.
- Probe output without no_legal_conclusion.

## Future implementation test plan

- Unit tests with mocked HTTP responses.
- Integration tests behind explicit network opt-in flag.
- validate-all must pass after probe artifacts are added.
