# What the 500 ESA evidence cards show

The ESA factory campaign converts 25 official mission landing pages into 500
small, independently inspectable source-boundary records. It was built to test
whether ClaimBound can scale beyond a few hand-picked examples without hiding
missing source coverage or turning a page match into a scientific endorsement.

## Result

| Measure | Result |
| --- | ---: |
| Factory cards | 500 |
| Official ESA mission pages | 25 |
| Frozen gates per mission | 20 |
| `PASSED_UNDER_PROTOCOL` | 490 |
| `INSUFFICIENT_COVERAGE` | 10 |
| Raw ESA payloads committed | 0 |
| Total cards in the repository registry | 548 |
| ESA cards in the repository registry | 505 |

The five ESA cards outside the factory campaign are earlier showcase records.
The complete machine-readable campaign summary is
[esa_500_summary.json](esa_500_summary.json).

## The finding

All ten limited results have the same shape: the selected mission landing page
did not expose the frozen launch-site or launch-vehicle marker.

| Mission | Missing landing-page gates |
| --- | --- |
| Gaia | Launch site, launch vehicle |
| ExoMars | Launch site, launch vehicle |
| Mars Express | Launch site, launch vehicle |
| Rosetta | Launch site, launch vehicle |
| Cluster | Launch site, launch vehicle |

This does not mean those mission facts are false or unavailable elsewhere. It
means the chosen official landing page is insufficient for those exact gates.
That distinction is the point of ClaimBound: a source boundary is recorded
instead of silently widening the search until a desired answer appears.

## Why these cards exist

The campaign provides four reusable assets:

1. A machine-readable map from a narrow public claim to one official source,
   one frozen gate, one exact status and one sanitized evidence card.
2. A baseline for source drift. A future rerun can show which mission pages,
   story titles, dates or metadata fields changed.
3. A completeness audit. Cross-mission statistics reveal which fields official
   landing pages expose consistently and which require deeper documentation.
4. A reproducibility test for ClaimBound itself. One workflow produced and
   validated hundreds of cards without committing raw source payloads.

The cards do not rank ESA missions, certify scientific results or imply ESA
endorsement. They make the public evidence boundary visible and challengeable.

## What to build next

The strongest next presentation is an evidence atlas rather than a carousel of
500 tiny cards:

- a 25 x 20 mission-by-gate heatmap with filters for status and topic;
- source-drift timelines after scheduled reruns;
- cross-mission completeness scores that remain clearly separate from science
  or mission-performance scores;
- a small "show me the gap" interaction that opens the ten limited cards;
- downloadable JSON/CSV slices for journalists and public-data reviewers.

Animation should explain state change, such as a rerun moving from pass to
limited coverage. Decorative card motion would attract attention but weaken the
audit-first message and make 500 records harder to scan.
