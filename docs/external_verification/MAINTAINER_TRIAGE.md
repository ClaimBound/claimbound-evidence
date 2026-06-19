# Maintainer Triage For VERIFY Issues

Use this when external operators post pack reports.

## Close When

| Issue | Close after external operator confirms |
| --- | --- |
| #85 | Baseline + starter demos + three flagship cards read |
| #89 | Four AI cards reviewed; no overclaim in boundaries |
| #90 | Registry validators exit 0; API parity card boundary narrow |
| #91 | SourceProbe spec is design-only; no false implementation claim |
| #92 | Static registry spec is design-only; no views generator shipped |
| #88 | EEA drift probe run; drift/no-drift documented honestly |
| #86 | NASA gate reproduced or mismatch documented |
| #87 | NOAA negative gate reproduced or mismatch documented |

## Do Not Close When

- Only baseline passed but pack-specific commands were skipped.
- Operator is the same handle as maintainer rerun cards without disclosure.
- Issue is closed as "spec verified" but body implied runtime reproduction (#91, #92).

## After All Eight Close

- Update [REVIEWER_SUMMARY.md](../REVIEWER_SUMMARY.md) only if verification level changes.
- Independent rerun PRs remain optional; VERIFY closure does not require a new card.