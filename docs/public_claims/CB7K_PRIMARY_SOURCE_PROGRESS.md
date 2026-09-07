# CB7K Primary-Source Progress

## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **6,230 / 7,000** |
| Remaining | **770** (11 domains × 70) |
| Next domain | **DOM090** Journalism |
| Last updated | 2026-09-07 |

## Summary

| Band | Domains | Cards | Protocol |
|---|---|---|---|
| Done | DOM001–DOM089 | 6,230 | primary-source manifests under `artifacts/cb7k_dom*_t*_primary_claims.json` |
| Remaining | DOM090–DOM100 | 770 | replace Wikidata-backed PASS with primary-source packs |

Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.

Latest packs:
- DOM089 Academic publishing — STM Report 2018: An overview of scientific and scholarly publishing (Fifth edition) (2026-09-07)
- DOM088 Open science — OECD Open Science - Enabling Discovery in the Digital Age (Going Digital Toolkit note) (2026-09-07)
- DOM087 Universities — OECD Education at a Glance 2025: OECD Indicators (special focus on tertiary education) (2026-09-07)
- DOM086 Education — UNESCO Global Education Monitoring Report 2024/5: Leadership in education – Lead for learning (2026-09-07)
- DOM085 Disaster response — IFRC World Disasters Report 2026: Truth, Trust and Humanitarian Action in the Age of Harmful Information (2026-09-07)
- DOM084 Weather services — WMO State of the Global Climate 2024 (WMO-No. 1368) (2026-09-07)
- DOM083 Earth observation — CEOS Earth Observation Handbook 2023: Space Data for the Global Stocktake (2026-09-07)
- DOM082 Satellites — NASA-STD-8719.14C Process for Limiting Orbital Debris (2026-09-07)
- DOM081 Urban planning — UN-Habitat World Cities Report 2024: Cities and Climate Action (2026-09-07)
- DOM080 Construction — IEA Material Efficiency in Clean Energy Transitions (2026-09-07)
- DOM079 Housing — UN-Habitat World Cities Report 2026: The Global Housing Crisis (2026-09-07)
- DOM078 Buildings — UNEP Global Status Report for Buildings and Construction 2025–2026 (2026-09-07)
- DOM077 Electric vehicles — IEA Global EV Outlook 2026 (2026-09-07)
- DOM076 Logistics — World Bank Connecting to Compete 2025 LPI 2.0 (2026-09-07)
- DOM075 Shipping — IPCC AR5 WGIII Chapter 8 Transport (2026-09-07)
- DOM074 Road safety — WHO Global Status Report on Road Safety 2023 (2026-09-07)



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

Next domain: **DOM090** Journalism.

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
