"""Assemble atlas HTML pages and results.json from loaded claim rows."""
from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from .constants import PRIMARY_SCHEMA, PRIMARY_SCOPE, REPO
from .load import load
from .pages import (
    audit_page,
    category_metrics,
    home_page,
    primary_claim_html,
    shell,
    tile_copy,
    wikidata_claim_html,
    esc,
)


def result_payload(manifest: dict, rows: list[dict], results: list[dict], grouped: dict) -> dict:
    primary_count = sum(row["source_kind"] == "primary" for row in rows)
    wikidata_count = len(rows) - primary_count
    reference_bound = sum(row["wikidata_reference_count"] > 0 for row in rows)
    qualified = sum(row["wikidata_qualifier_count"] > 0 for row in rows)
    if primary_count == 7000:
        schema_version, verification_scope = PRIMARY_SCHEMA, PRIMARY_SCOPE
    elif primary_count > wikidata_count:
        schema_version = PRIMARY_SCHEMA
        verification_scope = (
            f"mixed: {primary_count} primary PDF statements; "
            f"{wikidata_count} Wikidata revision publication bindings"
        )
    else:
        schema_version = manifest["schema_version"]
        verification_scope = manifest["verification_scope"]
    return {
        "schema_version": schema_version,
        "maintainer": "NeoZorK",
        "claim_count": len(results),
        "category_count": len(grouped),
        "distinct_statement_count": len({row["statement_id"] for row in rows}),
        "distinct_revision_count": len(
            {row["revision_id"] for row in rows if row["source_kind"] == "wikidata"}
        ),
        "primary_statement_count": primary_count,
        "wikidata_statement_count": wikidata_count,
        "result_counts": dict(Counter(row["result_status"] for row in results)),
        "verification_scope": verification_scope,
        "reference_bound_statement_count": reference_bound,
        "qualified_statement_count": qualified,
        "independent_reproduction_count": 0,
        "results": results,
    }


def build(output: Path) -> None:
    manifest, rows = load()
    if output.exists():
        shutil.rmtree(output)
    (output / "categories").mkdir(parents=True)
    (output / "audit").mkdir()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["domain_slug"]].append(row)
    primary_total = sum(row["source_kind"] == "primary" for row in rows)
    wikidata_total = len(rows) - primary_total
    reference_bound = sum(row["wikidata_reference_count"] > 0 for row in rows)
    qualified = sum(row["wikidata_qualifier_count"] > 0 for row in rows)
    tiles: list[str] = []
    results: list[dict] = []
    for slug, category_rows in grouped.items():
        first = category_rows[0]
        claims = []
        for index, row in enumerate(category_rows, 1):
            card = row["card"]
            card_url = f"{REPO}/blob/main/{row['card_path']}"
            if row["source_kind"] == "primary":
                claims.append(primary_claim_html(index, row, card, card_url))
            else:
                claims.append(wikidata_claim_html(index, row, card, card_url))
            results.append(
                {key: value for key, value in row.items() if key not in {"card"}}
                | {"evidence_id": card["evidence_id"], "result_status": card["result_status"]}
            )
        primary_count = sum(row["source_kind"] == "primary" for row in category_rows)
        reference_count = sum(row["wikidata_reference_count"] > 0 for row in category_rows)
        category_body = (
            f"<p>CLAIMBOUND / SOURCE-PUBLICATION EVIDENCE</p><h1>{esc(first['domain_title'])}</h1>"
            f'<div class="alert"><strong>70 distinct source statements, not 70 independently proven facts.</strong> '
            f"{primary_count} results use an official primary source; "
            f"{70 - primary_count} retain their explicitly limited Wikidata publication boundary.</div>"
            '<p class="lede">Every card identifies what it proves, what it does not prove, '
            "its exact quote, locator, source hash, and local rerun command.</p>"
            f'<section class="grid">{category_metrics(primary_count, reference_count)}</section>'
            f'<section class="claims">{"".join(claims)}</section>'
        )
        category_dir = output / "categories" / slug
        category_dir.mkdir()
        (category_dir / "index.html").write_text(
            shell(first["domain_title"], category_body, "../../"), encoding="utf-8"
        )
        tiles.append(
            f'''<article class="tile"><h2><a href="categories/{esc(slug)}/">'''
            f'''{esc(first['domain_title'])}</a></h2><p>{tile_copy(primary_count)}</p></article>'''
        )
    payload = result_payload(manifest, rows, results, grouped)
    (output / "results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "index.html").write_text(
        shell(
            "7,000 public claims",
            home_page(primary_total, wikidata_total, reference_bound, tiles),
        ),
        encoding="utf-8",
    )
    (output / "audit/index.html").write_text(
        shell(
            "Verification audit",
            audit_page(primary_total, wikidata_total, reference_bound, qualified),
            "../",
        ),
        encoding="utf-8",
    )
    print(
        f"Built {len(results)} claims across {len(grouped)} category pages "
        f"({primary_total} primary)"
    )
