# EEA source drift check (2026-06-15)

Original card: `docs/evidence_cards/CLAIMBOUND-SOURCE_AUDIT_D001-2026-05-08.json`
Baseline: `artifacts/source_audit_d001_summary.json`
Fresh: `artifacts/eea_source_audit_drift_check_summary.json`

## Drift observed?

**YES** — `page_sha256` changed while HTTP status, title, byte size and link-presence gates remained stable.

| Field | Baseline | Fresh (2026-06-15) |
| --- | --- | --- |
| `http_status` | 200 | 200 |
| `final_url` | `https://aqportal.discomap.eea.europa.eu/download-data/` | same |
| `page_byte_size` | 85123 | 85123 |
| `page_sha256` | `beb658db…` | `24446e82…` |
| `rights_link_present` | true | true |
| `result_status` | PASSED_UNDER_PROTOCOL | PASSED_UNDER_PROTOCOL |

## Changed fields

- `page_sha256` (source-byte drift on HTML payload)

## Card boundary impact

Source drift only. The frozen source-audit gate still passes: page reachable, expected download links present, rights link found. No dataset download or legal conclusion is claimed.

## Forbidden claim

The original card is **not** invalid solely because HTML bytes drifted. Do not claim full byte-identical reproduction without a new reproduction card.
