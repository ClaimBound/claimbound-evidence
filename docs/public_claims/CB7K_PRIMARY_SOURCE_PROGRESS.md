# CB7K Primary-Source Progress

## Counter

| Metric | Value |
|---|---|
| Primary-backed done | **6,440 / 7,000** |
| Remaining | **560** (8 domains × 70) |
| Next domain | **DOM093** Consumer products |
| Last updated | 2026-09-07 |

## Summary

| Band | Domains | Cards | Protocol |
|---|---|---|---|
| Done | DOM001–DOM092 | 6,440 | primary-source manifests under `artifacts/cb7k_dom*_t*_primary_claims.json` |
| Remaining | DOM093–DOM100 | 560 | replace Wikidata-backed PASS with primary-source packs |

Target: **7,000 / 7,000** primary-backed `PASSED_UNDER_PROTOCOL` cards.

Latest packs:
- DOM092: E-commerce — UNCTAD Digital Economy Report 2024 Chapter V: E-commerce and environmental sustainability

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

Next domain: **DOM093** Consumer products.

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
