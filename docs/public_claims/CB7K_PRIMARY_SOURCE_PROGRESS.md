# CB7K Primary-Source Progress

## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **5,600 / 7,000** |
| Remaining | **1,400** (20 domains × 70) |
| Next domain | **DOM081** Urban planning |
| Last updated | 2026-09-07 |

## Summary

| Band | Domains | Cards | Protocol |
|---|---|---|---|
| Done | DOM001–DOM080 | 5,600 | primary-source manifests under `artifacts/cb7k_dom*_t*_primary_claims.json` |
| Remaining | DOM081–DOM100 | 1,400 | replace Wikidata-backed PASS with primary-source packs |

Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.

Latest packs:
- DOM068 Oil and gas — IPCC AR4 WGIII Ch4 + AR5 WGIII Ch7 (2026-09-07)
- DOM069 Batteries — IRENA Electricity Storage and Renewables Costs and Markets to 2030 (2026-09-07)
- DOM070 Hydrogen — IRENA Hydrogen: A renewable energy perspective (2026-09-07)
- DOM071 Aviation — IPCC AR5 WGIII Chapter 8 Transport (2026-09-07)
- DOM072 Rail — IEA The Future of Rail (2026-09-07)
- DOM073 Public transit — IEA Bus Systems for the Future (2026-09-07)
- DOM074 Road safety — WHO Global Status Report on Road Safety 2023 (2026-09-07)
- DOM075 Shipping — IPCC AR5 WGIII Chapter 8 Transport (2026-09-07)
- DOM076 Logistics — World Bank Connecting to Compete 2025 LPI 2.0 (2026-09-07)
- DOM077 Electric vehicles — IEA Global EV Outlook 2026 (2026-09-07)
- DOM078 Buildings — UNEP Global Status Report for Buildings and Construction 2025–2026 (2026-09-07)
- DOM079 Housing — UN-Habitat World Cities Report 2026: The Global Housing Crisis (2026-09-07)
- DOM080 Construction — IEA Material Efficiency in Clean Energy Transitions (2026-09-07)

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

Next domain: **DOM081** Urban planning.

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
