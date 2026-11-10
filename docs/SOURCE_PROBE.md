# SourceProbe v1

SourceProbe is a small, metadata-only check of one public source URL. It helps a
human decide whether a source is worth a full protocol. It is not evidence by
itself and makes no legal conclusion.

## Usage

```bash
uv run claimbound probe URL [--marker TEXT ...] [--out FILE] [--json]
python scripts/claimbound_source_probe.py URL --marker "Download"
```

Only `http` and `https` are accepted. Standard library `urllib` only. The probe
sends `User-Agent: claimbound-source-probe`, uses a 15 s timeout and reads at
most 1 MiB. The response body is never written to disk; only metadata is kept.

## Fields

- `url`, `final_url` (after redirects), `http_status`, `content_type`, `byte_size`
- `body_fully_read`, `sha256` (only when the body was fully read under the cap, else `null`)
- `expected_marker_checks`: list of `{marker, found}`, case-sensitive substring search
- `license_or_terms_links`: link hints only (up to 20)
- `robots_disallow_hint`: robots.txt disallows the URL for this User-Agent
- `recommendation`: `safe_to_continue` | `needs_human_review` | `blocked`
  (`blocked` on 401/403/429/5xx, captcha-like markers, robots disallow, or request failure)
- `reasons`, `no_legal_conclusion` (always `true`), `probed_at_utc`

`validate_probe_artifact()` in `claimbound_evidence.source_probe` checks a saved artifact.

## Non-goals

- Never emits `PASSED_UNDER_PROTOCOL` or any PASS status.
- No legal reuse conclusions; link hints are not a rights assessment.
- Does not replace a human-reviewed protocol or card boundary.
- Does not store raw payloads.
