# ESA issues #133-#135: remaining 300 cards

This runbook covers the final three batches in the 500-card ESA factory:

- #133: SMOS, Aeolus, CryoSat, Euclid and Gaia;
- #134: Juice, BepiColombo, ExoMars, Mars Express and Cheops;
- #135: Ariel, Plato, XMM-Newton, Rosetta and Cluster.

Each issue contains 100 unique source-boundary gates: 20 gates against each of
five official ESA mission pages. Raw HTML stays in `~/claimbound_runs/` and is
never committed.

## 1. Check the frozen matrices

```bash
uv sync --extra dev
uv run claimbound doctor

for ISSUE in 133 134 135; do
  uv run python scripts/claimbound_run_esa_factory.py \
    --issue "$ISSUE" check
done
```

Each issue must report `matrix_cards=100` and `matrix_status=VALID`.

## 2. Create local-only previews

Run one issue at a time and retain the printed path:

```bash
uv run python scripts/claimbound_run_esa_factory.py \
  --issue 133 preview
```

The preview fetches five official ESA pages, hashes the raw responses and
evaluates all 100 frozen gates without changing repository files.

Review every non-pass before publication:

```bash
jq -r '
  .results[]
  | select(.result_status != "PASSED_UNDER_PROTOCOL")
  | [.protocol_id, .mission, .topic, .result_status,
     (.missing_patterns | join(" | "))]
  | @tsv
' <preview.json>
```

Do not alter a gate after seeing its result. If a matrix needs correction,
change it explicitly and create a new preview.

## 3. Publish a reviewed issue

```bash
uv run python scripts/claimbound_run_esa_factory.py \
  --issue 133 publish \
  --preview <preview.json> \
  --operator <github-handle> \
  --confirm-reviewed
```

Publish #133, #134 and #135 sequentially because each publication allocates
new registry sequence numbers.

## 4. Validate the repository

```bash
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
git diff --check
```

Confirm that no raw payload entered the repository:

```bash
if git status --short | grep -Eq '\.html$|/raw/'; then
  echo "ERROR: raw ESA payload is inside the repository"
  false
else
  echo "OK: no raw ESA HTML is inside the repository"
fi
```

## 5. Rebuild the campaign summary

After all five batch summaries (#131-#135) exist:

```bash
uv run python scripts/build_esa_factory_showcase.py
```

The command verifies 500 unique campaign protocol IDs against the registry and
regenerates:

- `docs/esa/esa_500_summary.json`;
- `docs/assets/esa_500_landscape.svg`.
