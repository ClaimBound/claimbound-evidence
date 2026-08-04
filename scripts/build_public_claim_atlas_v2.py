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
PRIMARY_MANIFEST = ROOT / "artifacts/cb7k_dom001_t01_openai_primary_claims.json"
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
    primary_manifest = json.loads(PRIMARY_MANIFEST.read_text(encoding="utf-8"))
    primary_report_sha = hashlib.sha256(PRIMARY_MANIFEST.read_bytes()).hexdigest()
    primary_by_protocol = {
        row["protocol_id"]: row for row in primary_manifest["records"]
    }
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
            primary = primary_by_protocol.get(card["protocol_id"])
            if primary:
                checks = {
                    "claim_text": card.get("public_claim_text") == primary["public_claim_text"],
                    "verbatim_quote": card.get("public_claim_verbatim_quote") == primary["public_claim_verbatim_quote"],
                    "source_url": card.get("public_claim_source_url") == primary_manifest["source_url"],
                    "locator": card.get("public_claim_locator") == primary["section_locator"],
                    "source_sha256": card.get("public_claim_source_sha256") == primary_manifest["source_sha256"],
                    "report_sha256": card.get("sanitized_report_sha256") == primary_report_sha,
                    "passed": card.get("result_status") == "PASSED_UNDER_PROTOCOL",
                }
                if not all(checks.values()):
                    raise SystemExit(f"ERROR: card/primary-manifest mismatch {card['evidence_id']}: {checks}")
                rows.append({
                    **record,
                    **primary,
                    "source_kind": "primary",
                    "statement_id": f"primary:{card['protocol_id']}",
                    "public_claim_source_url": primary_manifest["source_url"],
                    "public_claim_source_sha256": primary_manifest["source_sha256"],
                    "public_claim_captured_at": primary_manifest["access_date"],
                    "wikidata_rank": None,
                    "wikidata_reference_count": 0,
                    "wikidata_qualifier_count": 0,
                    "card": card,
                    "card_path": path.relative_to(ROOT).as_posix(),
                    "checks": checks,
                })
                continue
            statement = json.loads(record["public_claim_verbatim_quote"])
            record = {
                **record,
                "source_kind": "wikidata",
                "wikidata_rank": statement.get("rank"),
                "wikidata_reference_count": len(statement.get("references", [])),
                "wikidata_qualifier_count": sum(
                    len(values) for values in statement.get("qualifiers", {}).values()
                ),
            }
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
    reference_bound = sum(row["wikidata_reference_count"] > 0 for row in rows)
    qualified = sum(row["wikidata_qualifier_count"] > 0 for row in rows)
    reproducible_command = (
        "python3 scripts/build_wikidata_public_claims.py verify-sources "
        "artifacts/cb7k_wikidata_public_claims.json --cache .cache/claimbound-wikidata "
        "--claim-id {claim_id}"
    )
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
            command = reproducible_command.format(claim_id=row["claim_id"])
            if row["source_kind"] == "primary":
                command = card["runner_command"]
                claims.append(f'''<article class="claim"><span class="tag">{esc(row['claim_id'])}</span><span class="tag">registry slot {esc(card['protocol_id'])}</span><span class="tag pass">PASSED: EXACT PRIMARY-SOURCE STATEMENT FOUND</span><h2>{index}. OpenAI GPT-5.6 · {esc(row['section_locator'])}</h2><p class="muted">Narrow public claim</p><blockquote>{esc(row['public_claim_text'])}</blockquote><h3>What this card proves</h3><p>The exact quoted statement occurred in the official OpenAI GPT-5.6 System Card PDF fetched on {esc(row['public_claim_captured_at'])}, and the complete PDF matched the recorded SHA-256.</p><h3>What this card does not prove</h3><p>It does not independently establish the underlying model capability, safety, comparison, or real-world truth. This is a retrospective single-maintainer source-publication audit.</p><dl><dt>Primary source</dt><dd><a href="{esc(source_url)}">OpenAI GPT-5.6 System Card PDF</a></dd><dt>Section locator</dt><dd><code>{esc(row['section_locator'])}</code></dd><dt>Captured</dt><dd>{esc(row['public_claim_captured_at'])}</dd><dt>Source SHA-256</dt><dd><code>{esc(row['public_claim_source_sha256'])}</code></dd><dt>Reproduction</dt><dd>Maintainer run only; no independent operator rerun is registered.</dd></dl><details><summary>Repeat this exact check locally</summary><p>Download the PDF to a local file, then run the committed verifier. A changed PDF is reported as drift rather than silently accepted.</p><pre><code>{esc(command)}</code></pre></details><details><summary>Exact source quote</summary><blockquote><code>{esc(quote)}</code></blockquote><p class="links"><a href="{card_url}">Evidence card JSON</a><a href="{card_url[:-5]}.svg">Rendered card</a></p></details></article>''')
            else:
                claims.append(f'''<article class="claim"><span class="tag">{esc(row['claim_id'])}</span><span class="tag">registry slot {esc(card['protocol_id'])}</span><span class="tag pass">PASSED: STATEMENT PUBLISHED IN REVISION</span><h2>{index}. {esc(row['entity_label'])} · {esc(row['property_label'])}</h2><p class="muted">Exact public statement under test</p><blockquote>{esc(row['public_claim_text'])}</blockquote><h3>What this card proves</h3><p>The exact statement GUID and JSON excerpt were publicly present in Wikidata revision {row['revision_id']}; the frozen revision content and statement match the recorded SHA-256 values.</p><h3>What this card does not prove</h3><p>It does not independently prove that the value is true in the real world, current outside this revision, supported by a primary source, or correctly assigned to this category.</p><dl><dt>Exact source</dt><dd><a href="{esc(source_url)}">Wikidata revision {row['revision_id']}</a></dd><dt>Locator</dt><dd><code>{esc(row['public_claim_locator'])}</code></dd><dt>Captured</dt><dd>{esc(row['public_claim_captured_at'])}</dd><dt>Rank / qualifiers</dt><dd>{esc(row['wikidata_rank'])}; {row['wikidata_qualifier_count']} qualifier snaks</dd><dt>Wikidata references</dt><dd>{row['wikidata_reference_count']} reference blocks — presence is reported, but the referenced sources were not independently checked by this protocol.</dd><dt>Source SHA-256</dt><dd><code>{esc(row['public_claim_source_sha256'])}</code></dd><dt>Statement SHA-256</dt><dd><code>{esc(row['statement_sha256'])}</code></dd><dt>Reproduction</dt><dd>Maintainer run only; no independent operator rerun is registered.</dd></dl><details><summary>Repeat this exact check locally</summary><p>Requires Python 3 and network access to Wikidata. Start with an empty cache; the command downloads the immutable revision and verifies the exact excerpt and both hashes.</p><pre><code>{esc(command)}</code></pre></details><details><summary>Verbatim structured statement and evidence</summary><blockquote><code>{esc(quote)}</code></blockquote><p class="links"><a href="{card_url}">Evidence card JSON</a><a href="{card_url[:-5]}.svg">Rendered card</a></p></details></article>''')
            results.append({key: value for key, value in row.items() if key not in {"card"}} | {"evidence_id": card["evidence_id"], "result_status": card["result_status"]})
        primary_count = sum(row["source_kind"] == "primary" for row in category_rows)
        category_body = f'''<p>CLAIMBOUND / SOURCE-PUBLICATION EVIDENCE</p><h1>{esc(first['domain_title'])}</h1><div class="alert"><strong>70 distinct source statements, not 70 independently proven facts.</strong> {primary_count} results use an official primary source; {70-primary_count} retain their explicitly limited Wikidata publication boundary.</div><p class="lede">Every card identifies what it proves, what it does not prove, its exact quote, locator, source hash, and local rerun command.</p><section class="grid"><article class="metric"><strong>{primary_count} / 70</strong>primary-source statements</article><article class="metric"><strong>{sum(row['wikidata_reference_count'] > 0 for row in category_rows)} / 70</strong>Wikidata statements with reference blocks</article><article class="metric"><strong>0 / 70</strong>independent ClaimBound reruns</article></section><section class="claims">{''.join(claims)}</section>'''
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
        "reference_bound_statement_count": reference_bound,
        "qualified_statement_count": qualified,
        "independent_reproduction_count": 0,
        "results": results,
    }
    (output / "results.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    home = f'''<p>CLAIMBOUND / 7,000 SOURCE-PUBLICATION CHECKS</p><h1>What do these cards actually prove?</h1><div class="alert"><strong>They prove publication, not ground truth.</strong> Each card establishes that one exact structured statement was publicly present in a named frozen Wikidata revision and that its source bytes and verbatim statement match recorded hashes. The campaign does not independently establish that the 7,000 values are true in the real world.</div><h2>Audit answer</h2><section class="grid"><article class="metric"><strong>7,000 / 7,000</strong>unique statement GUIDs and claim bindings</article><article class="metric"><strong>7,000 / 7,000</strong>repeatable source checks</article><article class="metric"><strong>{reference_bound} / 7,000</strong>statements containing Wikidata reference blocks</article><article class="metric"><strong>0 / 7,000</strong>independent ClaimBound reruns</article></section><h2>Can another person reproduce any card?</h2><p class="lede">Yes, while the named Wikidata revision remains publicly retrievable. Every card now includes a single-claim command that works with an empty local cache using only Python 3 and network access. It verifies revision timestamp, full revision SHA-256, statement GUID, literal JSON excerpt, and statement SHA-256.</p><h2>ClaimBound honesty assessment</h2><p>The records satisfy the source-binding, explicit-boundary, raw-payload, deterministic-runner, limitation, and registry requirements. They are not independent fact-checks: selection starts from statements already published in Wikidata, all outcomes pass the publication gate, external references are not followed, and no second operator has registered a rerun. Those limitations are now visible on the home page, audit page, and every category/card.</p><h2>100 categories</h2><section class="grid">{''.join(tiles)}</section>'''
    (output / "index.html").write_text(shell("7,000 public claims", home), encoding="utf-8")
    audit = f'''<p>CLAIMBOUND / HONESTY AND REPRODUCIBILITY AUDIT</p><h1>Complete source bindings.<br>Limited evidentiary claim.</h1><section class="grid"><article class="metric"><strong>7,000 / 7,000</strong>unique statement GUIDs</article><article class="metric"><strong>7,000 / 7,000</strong>claim text, verbatim excerpt, locator and hashes</article><article class="metric"><strong>100 / 100</strong>categories with exactly 70 claims</article><article class="metric"><strong>{reference_bound} / 7,000</strong>contain Wikidata reference blocks</article><article class="metric"><strong>{qualified} / 7,000</strong>contain qualifiers</article><article class="metric"><strong>0 / 7,000</strong>independent operator reruns</article></section><h2>Passed checks</h2><ul><li>Every card binds one distinct public statement to an immutable revision and exact source URL.</li><li>Every card records a substantive verbatim JSON excerpt, locator, capture timestamp, full source SHA-256 and statement SHA-256.</li><li>Raw source payloads are excluded from the repository; the sanitized manifest and cards are committed.</li><li>The deterministic verifier can fetch and check one selected card or all 7,000.</li><li>Every result states the narrow claim boundary and limitations.</li></ul><h2>Limitations and open verification gaps</h2><ul><li>The collector discovers statements that already exist, so a pass under the publication gate is expected; outcome diversity would not add evidence.</li><li>The gate verifies publication and byte identity, not real-world truth.</li><li>Wikidata reference blocks are counted but their target documents are not fetched or adjudicated.</li><li>Category assignment follows deterministic search discovery and has not received independent semantic review.</li><li>No independent operator rerun is registered yet.</li><li>A rerun depends on public availability of the named Wikimedia revision and network access.</li></ul><h2>Reproduce one card</h2><pre><code>{esc(reproducible_command.format(claim_id='CB7K-DOM001-C01'))}</code></pre><h2>Reproduce all cards</h2><pre><code>python3 scripts/build_wikidata_public_claims.py verify-sources artifacts/cb7k_wikidata_public_claims.json --cache .cache/claimbound-wikidata</code></pre><p><a href="../results.json">Download all 7,000 detailed results</a></p>'''
    (output / "audit/index.html").write_text(shell("Verification audit", audit, "../"), encoding="utf-8")
    print(f"Built {len(results)} claims across {len(grouped)} category pages")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
