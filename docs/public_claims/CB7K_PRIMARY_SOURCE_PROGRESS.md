# CB7K Primary-Source Progress

## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **4,480 / 7,000** |
| Remaining | **2,520** (36 domains × 70) |
| Next domain | **DOM065** Renewable energy |
| Last updated | 2026-09-06 |

## Summary

| Band | Domains | Cards | Protocol |
|---|---|---|---|
| Done | DOM001–DOM064 | 4,480 | primary-source manifests under `artifacts/cb7k_dom*_t*_primary_claims.json` |
| Remaining | DOM065–DOM100 | 2,520 | replace Wikidata-backed PASS with primary-source packs |

Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.

Latest packs:
- **DOM060** Mining — IPCC AR4 WGIII Ch4+Ch7 (2026-09-05)
- **DOM061** Chemicals — IPCC AR5 WGIII Ch10 + AR4 WGIII Ch7 (2026-09-06)
- **DOM062** Waste management — IPCC GPG Chapter 5 Waste (2026-09-06)
- **DOM063** Recycling — US EPA MSW Facts 2012 + IPCC AR4 WGIII Ch10 (2026-09-06)
- **DOM064** Plastics — OECD Global Plastics Outlook (2026-09-06)

## Cadence

One domain = 70 cards (7 topics × 10 gates).

```bash
# 1) inventory + local PDF (not committed) under tmp/primary_sources/domNNN/a.pdf
# 2) build manifests
python3 scripts/build_domain_primary_claim_manifests.py \
  --source-root tmp/primary_sources \
  --inventory artifacts/cb7k_domNNN_primary_source_inventory.json \
  --domain DOMNNN
# 3) verify each topic
python3 scripts/verify_primary_public_claim_group.py \
  artifacts/cb7k_domNNN_t01_primary_claims.json \
  --source-file tmp/primary_sources/domNNN/a.pdf
# 4) register each topic
python3 scripts/register_primary_public_claim_group.py \
  artifacts/cb7k_domNNN_t01_primary_claims.json
# 5) validate
uv run claimbound validate-all
uv run pytest tests -n auto
```

## Queue

Next domain: **DOM055** Oceans.

Waves:

- A DOM051–053 (done) → DOM054–060
- B DOM061–070
- C DOM071–080
- D DOM081–090
- E DOM091–100

## Honesty bar

PASS is allowed only when the frozen PDF SHA-256 matches and the exact quote
occurs in both the selecting extractor and the independent extractor. Publication
in fetched bytes is not independent ground truth.
