# CB7K Primary-Source Progress

## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **3,710 / 7,000** |
| Remaining | **3,290** (47 domains × 70) |
| Next domain | **DOM054** Water quality |
| Last updated | 2026-09-05 |

Status tracker for rewriting all 7,000 CB7K registry slots onto the
primary-source publication protocol (exact verbatim quote + full-source
SHA-256 + dual-extractor verification).

## Summary

| Band | Domains | Cards | Protocol |
|---|---|---|---|
| Done | DOM001–DOM053 | 3,710 | primary-source manifests under `artifacts/cb7k_dom*_t*_primary_claims.json` |
| Remaining | DOM054–DOM100 | 3,290 | replace Wikidata-backed PASS with primary-source packs |

Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.

Latest packs:
- **DOM051** Climate science — IPCC AR6 SYR SPM (2026-09-05)
- **DOM052** Carbon offsets — World Bank State and Trends of Carbon Pricing 2024 (2026-09-05)
- **DOM053** Air quality — World Bank The Cost of Air Pollution (2026-09-05)

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

Next domain: **DOM054** (Water quality).

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
