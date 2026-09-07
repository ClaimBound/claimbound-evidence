# CB7K Primary-Source Progress

## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **4,830 / 7,000** |
| Remaining | **2,170** (31 domains × 70) |
| Next domain | **DOM070** Hydrogen |
| Last updated | 2026-09-07 |

## Summary

| Band | Domains | Cards | Protocol |
|---|---|---|---|
| Done | DOM001–DOM069 | 4,830 | primary-source manifests under `artifacts/cb7k_dom*_t*_primary_claims.json` |
| Remaining | DOM070–DOM100 | 2,170 | replace Wikidata-backed PASS with primary-source packs |

Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.

Latest packs:
- **DOM062** Waste management — IPCC GPG Chapter 5 Waste (2026-09-06)
- **DOM063** Recycling — US EPA MSW Facts 2012 + IPCC AR4 WGIII Ch10 (2026-09-06)
- **DOM064** Plastics — OECD Global Plastics Outlook (2026-09-06)
- **DOM065** Renewable energy — IPCC AR5 WGIII Ch7 Energy Systems (2026-09-06)
- **DOM066** Power grid — IPCC AR5 WGIII Ch6 Assessing Transformation Pathways (2026-09-06)
- **DOM067** Nuclear energy — IAEA Nuclear Energy Series PUB1908 (2026-09-07)
- **DOM068** Oil and gas — IPCC AR4 WGIII Ch4 + AR5 WGIII Ch7 (2026-09-07)
- **DOM069** Batteries — IRENA Electricity Storage and Renewables Costs and Markets to 2030 (2026-09-07)

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
