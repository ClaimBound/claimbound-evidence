# Public Claim Candidate Catalog

This catalog expands ClaimBound with a preregistered backlog of **7,000 candidate
claims across 100 public-interest domains**.

The catalog is not evidence and does not add 7,000 green cards. Every record starts
as `PENDING_SOURCE_SELECTION`. Before the first network request, an operator must
select one exact public source URL, freeze the source manifest, and keep the original
claim and source even when the result is blocked, insufficient, negative, or later
drifts.

> **Registration rule (effective 2026-07-26):** a candidate question is never a
> public claim. A new evidence card is rejected unless it contains a concrete
> declarative claim, a substantive verbatim source excerpt, an exact HTTPS URL,
> a quote locator, capture time and the captured source SHA-256. The historical
> CB7K gate-question run therefore cannot be relabelled as 7,000 verified public
> claims; each item must first be replaced by a genuinely sourced statement and
> rerun under a frozen protocol.

## Revision-bound replacement campaign

The historical gate-question records have now been replaced in their existing
100 × 70 registry slots by 7,000 distinct structured public statements from
Wikidata. The sanitized manifest is
`artifacts/cb7k_wikidata_public_claims.json`; raw revision content remains in a
local cache and is not committed.

The narrow result is deliberately precise: `PASSED_UNDER_PROTOCOL` means the
exact statement GUID and verbatim JSON excerpt occur in the named Wikidata
revision and the frozen revision content matches the recorded SHA-256. It does
not mean that ClaimBound independently proved the value's real-world truth.

Reproduce the local source binding checks:

```bash
python3 scripts/build_wikidata_public_claims.py verify-sources \
  artifacts/cb7k_wikidata_public_claims.json \
  --cache /path/to/local-wikidata-cache
```

Reproduce one selected card from an empty cache:

```bash
python3 scripts/build_wikidata_public_claims.py verify-sources \
  artifacts/cb7k_wikidata_public_claims.json \
  --cache .cache/claimbound-wikidata \
  --claim-id CB7K-DOM001-C01
```

This rerun verifies source publication and byte identity. It does not validate
the statement against the real world, follow its reference blocks, or convert a
maintainer run into independent reproduction. Those are separate evidence
tracks and must be reported separately.

The collector uses a descriptive User-Agent, sequential requests, `maxlag=5`
and local caching. Wikidata structured data is published under CC0; see the
[Wikidata data-access documentation](https://www.wikidata.org/wiki/Help:Data_access)
and [MediaWiki API etiquette](https://www.mediawiki.org/wiki/API:Etiquette).

## Build locally

```bash
python3 scripts/build_public_claim_catalog.py validate
python3 scripts/build_public_claim_catalog.py build \
  --output tmp/public-claim-catalog
python3 -m http.server 8000 --directory tmp/public-claim-catalog
```

Open `http://localhost:8000`.

The build produces:

- `catalog.json` and `catalog.jsonl` with exactly 7,000 unique candidate records;
- one static page under `domains/<domain>/` for each of 100 domains;
- 34 GitHub issue-ready Markdown batches, each within GitHub's issue-body limit;
- prefilled per-claim “open verification issue” links.

## Freeze sources before fetching

Create a local source manifest:

```json
{
  "domain": "water-quality",
  "sources": [
    {
      "topic": "lead concentration",
      "source_url": "https://example.gov/exact-frozen-source"
    }
  ]
}
```

Then freeze it:

```bash
python3 scripts/build_public_claim_catalog.py \
  freeze-manifest tmp/water-quality-sources.json
```

Record the printed SHA-256 in the eventual protocol. Do not commit raw downloaded
payloads.

Before executing a batch, prepare a claim-level execution manifest. Every claim
must name its exact URL, gate-specific evaluation method, frozen parameters,
support rule and an explicit negative rule. A complete domain requires at least
one independently selected URL for each of its seven topics; one generic URL for
all 70 claims is rejected.

```bash
python3 scripts/build_public_claim_catalog.py \
  validate-execution-manifest tmp/batch-01-execution-manifest.json
```

The validator deliberately does not require a quota of passes or negatives.
Outcome diversity is not evidence; each status must follow its frozen gate.

## Publish issue batches

Preview only:

```bash
python3 scripts/build_public_claim_catalog.py publish-issues
```

After reviewing the generated bodies and confirming `gh auth status`:

```bash
python3 scripts/build_public_claim_catalog.py publish-issues --publish
```

This creates 34 issues covering all 7,000 candidates. It does not run any claim or
predeclare any result.

## Honest outcome boundary

Only these eventual outcomes are advertised by the catalog:

- `PASSED_UNDER_PROTOCOL`
- `INSUFFICIENT_COVERAGE`
- `NEGATIVE_RESULT_UNDER_PROTOCOL`
- `BLOCKED_SOURCE`
- `SOURCE_DRIFT`

A page-level pass is never general safety, quality, legal, scientific, or regulatory
certification.
