#!/usr/bin/env python3
"""Build GitHub Pages for the 7,000 revision-bound public claims."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifacts/cb7k_wikidata_public_claims.json"
CARDS = ROOT / "docs/evidence_cards"
REPO = "https://github.com/ClaimBound/claimbound-evidence"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def shell(title: str, body: str, root: str = "") -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · ClaimBound</title><style>
:root{{--ink:#142d32;--muted:#5c7074;--paper:#f2eee5;--card:#fffdf8;--line:#c9c2b4;--accent:#006d68;--pass:#217a55}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1280px;margin:auto;padding:28px 22px 80px}}a{{color:var(--accent)}}nav,.links{{display:flex;gap:14px;flex-wrap:wrap}}h1,h2{{font-family:Georgia,serif}}h1{{font-size:clamp(36px,6vw,68px);line-height:1.03}}.lede{{font-size:19px;max-width:960px}}.alert,.claim,.tile,.metric{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px}}.alert{{border:2px solid var(--accent)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:12px}}.claims{{display:grid;gap:16px}}.tag{{display:inline-block;padding:4px 9px;border-radius:99px;background:#e3ece8;margin:0 6px 6px 0;font-size:13px}}.pass{{background:var(--pass);color:white}}.metric strong{{display:block;font:700 30px Georgia,serif}}blockquote{{margin:10px 0;border-left:4px solid var(--accent);padding:4px 0 4px 14px;overflow-wrap:anywhere}}dl{{display:grid;grid-template-columns:210px 1fr;gap:7px 14px}}dt{{font-weight:700}}dd{{margin:0;overflow-wrap:anywhere}}details{{border-top:1px solid var(--line);padding-top:10px}}code{{overflow-wrap:anywhere}}small,.muted{{color:var(--muted)}}@media(max-width:650px){{dl{{grid-template-columns:1fr}}}}
</style></head><body><main><nav><a href="{root}index.html">All categories</a><a href="{root}audit/">Verification audit</a><a href="{REPO}">Repository</a></nav>{body}</main></body></html>'''


def load() -> tuple[dict, list[dict]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    rows: list[dict] = []
    card_paths = sorted(CARDS.glob("CLAIMBOUND-CB7K-*.json"))
    cards_by_protocol = {
        json.loads(path.read_text(encoding="utf-8"))["protocol_id"]: (path, json.loads(path.read_text(encoding="utf-8")))
        for path in card_paths
    }
    if len(cards_by_protocol) != 7000:
        raise SystemExit(f"ERROR: expected 7000 CB7K cards, got {len(cards_by_protocol)}")
    # Existing protocol slots are ordered T01/G01 ... T07/G10 within each domain.
    slots: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    for path, card in cards_by_protocol.values():
        domain_code = card["protocol_id"].split("-")[1]
        slots[domain_code].append((path, card))
    for values in slots.values():
        values.sort(key=lambda pair: pair[1]["protocol_id"])
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for record in manifest["records"]:
        by_domain[record["domain_code"]].append(record)
    for domain_code in sorted(by_domain):
        for record, (path, card) in zip(by_domain[domain_code], slots[domain_code], strict=True):
            checks = {
                "claim_text": card.get("public_claim_text") == record["public_claim_text"],
                "verbatim_quote": card.get("public_claim_verbatim_quote") == record["public_claim_verbatim_quote"],
                "source_url": card.get("public_claim_source_url") == record["public_claim_source_url"],
                "locator": card.get("public_claim_locator") == record["public_claim_locator"],
                "source_sha256": card.get("public_claim_source_sha256") == record["public_claim_source_sha256"],
                "report_sha256": card.get("sanitized_report_sha256") == report_sha,
                "passed": card.get("result_status") == "PASSED_UNDER_PROTOCOL",
            }
            if not all(checks.values()):
                raise SystemExit(f"ERROR: card/manifest mismatch {card['evidence_id']}: {checks}")
            rows.append({**record, "card": card, "card_path": path.relative_to(ROOT).as_posix(), "checks": checks})
    if len(rows) != 7000 or len({row["statement_id"] for row in rows}) != 7000:
        raise SystemExit("ERROR: atlas requires 7000 distinct statement IDs")
    return manifest, rows


def build(output: Path) -> None:
    manifest, rows = load()
    if output.exists():
        shutil.rmtree(output)
    (output / "categories").mkdir(parents=True)
    (output / "audit").mkdir()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["domain_slug"]].append(row)
    tiles: list[str] = []
    results: list[dict] = []
    for slug, category_rows in grouped.items():
        first = category_rows[0]
        claims = []
        for index, row in enumerate(category_rows, 1):
            card = row["card"]
            card_url = f"{REPO}/blob/main/{row['card_path']}"
            source_url = row["public_claim_source_url"]
            quote = row["public_claim_verbatim_quote"]
            claims.append(f'''<article class="claim"><span class="tag">{esc(card['protocol_id'])}</span><span class="tag pass">PASSED UNDER PUBLICATION PROTOCOL</span><h2>{index}. {esc(row['entity_label'])} · {esc(row['property_id'])}</h2><p class="muted">Concrete public claim</p><blockquote>{esc(row['public_claim_text'])}</blockquote><dl><dt>Exact source</dt><dd><a href="{esc(source_url)}">Wikidata revision {row['revision_id']}</a></dd><dt>Locator</dt><dd><code>{esc(row['public_claim_locator'])}</code></dd><dt>Captured</dt><dd>{esc(row['public_claim_captured_at'])}</dd><dt>Source SHA-256</dt><dd><code>{esc(row['public_claim_source_sha256'])}</code></dd><dt>Statement SHA-256</dt><dd><code>{esc(row['statement_sha256'])}</code></dd><dt>Result boundary</dt><dd>{esc(card['claim_boundary'])}</dd></dl><details><summary>Verbatim structured statement and evidence</summary><blockquote><code>{esc(quote)}</code></blockquote><p class="links"><a href="{card_url}">Evidence card JSON</a><a href="{card_url[:-5]}.svg">Rendered card</a></p></details></article>''')
            results.append({key: value for key, value in row.items() if key not in {"card"}} | {"evidence_id": card["evidence_id"], "result_status": card["result_status"]})
        category_body = f'''<p>CLAIMBOUND / PUBLIC CLAIMS</p><h1>{esc(first['domain_title'])}</h1><div class="alert"><strong>70 distinct claims.</strong> Each result verifies publication of one exact Wikidata statement in one frozen revision. It does not independently establish real-world truth.</div><p class="lede">Every card below includes its own statement GUID, verbatim JSON excerpt, immutable revision locator and hashes.</p><section class="claims">{''.join(claims)}</section>'''
        category_dir = output / "categories" / slug
        category_dir.mkdir()
        (category_dir / "index.html").write_text(shell(first["domain_title"], category_body, "../../"), encoding="utf-8")
        tiles.append(f'''<article class="tile"><h2><a href="categories/{esc(slug)}/">{esc(first['domain_title'])}</a></h2><p>70 distinct revision-bound public claims</p></article>''')
    result_payload = {
        "schema_version": manifest["schema_version"],
        "maintainer": "NeoZorK",
        "claim_count": len(results),
        "category_count": len(grouped),
        "distinct_statement_count": len({row["statement_id"] for row in rows}),
        "distinct_revision_count": len({row["revision_id"] for row in rows}),
        "result_counts": dict(Counter(row["result_status"] for row in results)),
        "verification_scope": manifest["verification_scope"],
        "results": results,
    }
    (output / "results.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    home = f'''<p>CLAIMBOUND / 7,000 PUBLIC CLAIMS</p><h1>100 categories.<br>7,000 source-bound statements.</h1><div class="alert"><strong>Exact scope:</strong> all 7,000 cards passed a publication-in-revision protocol. This verifies that each statement was publicly present in its named frozen Wikidata revision; it is not independent real-world fact checking.</div><section class="grid"><article class="metric"><strong>7,000</strong>distinct statement GUIDs</article><article class="metric"><strong>100</strong>categories</article><article class="metric"><strong>{result_payload['distinct_revision_count']}</strong>frozen revisions</article><article class="metric"><strong>0</strong>missing claim bindings</article></section><h2>Categories</h2><section class="grid">{''.join(tiles)}</section>'''
    (output / "index.html").write_text(shell("7,000 public claims", home), encoding="utf-8")
    audit = f'''<p>CLAIMBOUND / VERIFICATION AUDIT</p><h1>7,000 complete source bindings.</h1><section class="grid"><article class="metric"><strong>7,000 / 7,000</strong>unique statement GUIDs</article><article class="metric"><strong>7,000 / 7,000</strong>claim text fields</article><article class="metric"><strong>7,000 / 7,000</strong>verbatim excerpts</article><article class="metric"><strong>7,000 / 7,000</strong>revision URLs and SHA-256 bindings</article><article class="metric"><strong>100 / 100</strong>categories with 70 claims</article></section><div class="alert"><strong>Honesty boundary.</strong> The gate checks publication in a frozen source revision. It does not prove that Wikidata's value is correct, current outside that revision, or independently corroborated.</div><p><a href="../results.json">Download all 7,000 detailed results</a></p>'''
    (output / "audit/index.html").write_text(shell("Verification audit", audit, "../"), encoding="utf-8")
    print(f"Built {len(results)} claims across {len(grouped)} category pages")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
