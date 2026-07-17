# Public Claim Candidate Catalog

This catalog expands ClaimBound with a preregistered backlog of **7,000 candidate
claims across 100 public-interest domains**.

The catalog is not evidence and does not add 7,000 green cards. Every record starts
as `PENDING_SOURCE_SELECTION`. Before the first network request, an operator must
select one exact public source URL, freeze the source manifest, and keep the original
claim and source even when the result is blocked, insufficient, negative, or later
drifts.

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
