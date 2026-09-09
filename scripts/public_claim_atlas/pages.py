"""HTML page fragments for the public claim atlas."""
from __future__ import annotations

import html

from .constants import PRIMARY_VERIFY, REPO, WIKIDATA_VERIFY


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def shell(title: str, body: str, root: str = "") -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · ClaimBound</title><style>
:root{{--ink:#142d32;--muted:#5c7074;--paper:#f2eee5;--card:#fffdf8;--line:#c9c2b4;--accent:#006d68;--pass:#217a55}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1280px;margin:auto;padding:28px 22px 80px}}a{{color:var(--accent)}}nav,.links{{display:flex;gap:14px;flex-wrap:wrap}}h1,h2{{font-family:Georgia,serif}}h1{{font-size:clamp(36px,6vw,68px);line-height:1.03}}.lede{{font-size:19px;max-width:960px}}.alert,.claim,.tile,.metric{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px}}.alert{{border:2px solid var(--accent)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:12px}}.claims{{display:grid;gap:16px}}.tag{{display:inline-block;padding:4px 9px;border-radius:99px;background:#e3ece8;margin:0 6px 6px 0;font-size:13px}}.pass{{background:var(--pass);color:white}}.metric strong{{display:block;font:700 30px Georgia,serif}}blockquote{{margin:10px 0;border-left:4px solid var(--accent);padding:4px 0 4px 14px;overflow-wrap:anywhere}}dl{{display:grid;grid-template-columns:210px 1fr;gap:7px 14px}}dt{{font-weight:700}}dd{{margin:0;overflow-wrap:anywhere}}details{{border-top:1px solid var(--line);padding-top:10px}}code{{overflow-wrap:anywhere}}small,.muted{{color:var(--muted)}}@media(max-width:650px){{dl{{grid-template-columns:1fr}}}}
</style></head><body><main><nav><a href="{root}index.html">All categories</a><a href="{root}audit/">Verification audit</a><a href="{REPO}">Repository</a></nav>{body}</main></body></html>'''


def tile_copy(primary_count: int) -> str:
    wikidata_count = 70 - primary_count
    if primary_count == 70:
        return "70 primary-source statements"
    if primary_count == 0:
        return "70 distinct revision-bound public claims"
    return f"{primary_count} primary-source statements · {wikidata_count} Wikidata-bound"


def category_metrics(primary_count: int, reference_count: int) -> str:
    metrics = [
        f'<article class="metric"><strong>{primary_count} / 70</strong>primary-source statements</article>',
        '<article class="metric"><strong>0 / 70</strong>independent ClaimBound reruns</article>',
    ]
    if primary_count < 70:
        metrics.insert(
            1,
            f'<article class="metric"><strong>{reference_count} / 70</strong>'
            "Wikidata statements with reference blocks</article>",
        )
    return "".join(metrics)


def home_page(primary_count: int, wikidata_count: int, reference_bound: int, tiles: list[str]) -> str:
    if primary_count == 7000:
        alert = (
            "<strong>They prove primary-source publication, not ground truth.</strong> "
            "Each of the 7,000 cards binds an exact quoted statement to a named official "
            "primary PDF (SHA-256 + section locator). The campaign does not independently "
            "establish that the quoted facts are true in the real world."
        )
        metrics = (
            '<article class="metric"><strong>7,000 / 7,000</strong>primary-source statements</article>'
            '<article class="metric"><strong>100 × 70</strong>categories with primary PDF bindings</article>'
            '<article class="metric"><strong>0 / 7,000</strong>independent ClaimBound reruns</article>'
        )
        reproduce = (
            "Yes, with the named official PDF and the committed dual-extractor verifier. "
            "Every primary card includes a local runner command: download the PDF, then run "
            f"<code>{esc(PRIMARY_VERIFY)}</code>. A changed PDF is reported as drift. "
            "No independent operator rerun is registered yet."
        )
        honesty = (
            "The records satisfy the source-binding, explicit-boundary, raw-payload, "
            "deterministic-runner, limitation, and registry requirements. They are not "
            "independent fact-checks: each PASS is a retrospective single-maintainer "
            "source-publication audit under a dual-extractor PDF gate. Publication in "
            "fetched bytes is not ground truth, and no second operator has registered a rerun."
        )
    else:
        alert = (
            "<strong>They prove publication, not ground truth.</strong> "
            f"{primary_count:,} cards bind exact quotes to official primary PDFs; "
            f"{wikidata_count:,} retain a Wikidata revision publication boundary. "
            "Neither path independently establishes real-world truth."
        )
        metrics = (
            f'<article class="metric"><strong>{primary_count:,} / 7,000</strong>primary-source statements</article>'
            f'<article class="metric"><strong>{wikidata_count:,} / 7,000</strong>Wikidata revision bindings</article>'
            f'<article class="metric"><strong>{reference_bound:,} / 7,000</strong>Wikidata statements with reference blocks</article>'
            '<article class="metric"><strong>0 / 7,000</strong>independent ClaimBound reruns</article>'
        )
        reproduce = (
            "Primary cards use the dual-extractor PDF verifier on each card. "
            "Wikidata cards use the revision verifier while the named revision remains public. "
            "No independent operator rerun is registered yet."
        )
        honesty = (
            "Mixed primary and Wikidata publication gates are visible on every card. "
            "Neither gate is an independent fact-check; external references are not followed "
            "as ground truth, and no second operator has registered a rerun."
        )
    return (
        "<p>CLAIMBOUND / 7,000 SOURCE-PUBLICATION CHECKS</p>"
        "<h1>What do these cards actually prove?</h1>"
        f'<div class="alert">{alert}</div><h2>Audit answer</h2>'
        f'<section class="grid">{metrics}</section>'
        "<h2>Can another person reproduce any card?</h2>"
        f'<p class="lede">{reproduce}</p>'
        f"<h2>ClaimBound honesty assessment</h2><p>{honesty}</p>"
        f'<h2>100 categories</h2><section class="grid">{"".join(tiles)}</section>'
    )


def audit_page(primary_count: int, wikidata_count: int, reference_bound: int, qualified: int) -> str:
    if primary_count == 7000:
        metrics = (
            '<article class="metric"><strong>7,000 / 7,000</strong>primary-source PDF statements</article>'
            '<article class="metric"><strong>7,000 / 7,000</strong>exact quote, locator, and PDF SHA-256</article>'
            '<article class="metric"><strong>100 / 100</strong>categories with exactly 70 claims</article>'
            '<article class="metric"><strong>dual-extractor</strong>publication gate on every PASS</article>'
            '<article class="metric"><strong>0 / 7,000</strong>independent operator reruns</article>'
        )
        passed = (
            "<li>Every card binds one exact quoted statement to a named official primary PDF and source URL.</li>"
            "<li>Every card records a section locator, capture date, and complete PDF SHA-256.</li>"
            "<li>PASS requires the quote in both the selecting extractor and an independent extractor.</li>"
            "<li>Raw PDF bytes are excluded from the repository; sanitized manifests and cards are committed.</li>"
            "<li>Every result states the narrow claim boundary and limitations.</li>"
        )
        limits = (
            "<li>The gate verifies primary-PDF publication and byte identity, not real-world truth.</li>"
            "<li>Review design is retrospective and single-maintainer; it is not preregistered.</li>"
            "<li>Dual-extractor agreement is a publication check, not an independent fact-check.</li>"
            "<li>No independent operator rerun is registered yet.</li>"
            "<li>A rerun needs the named official PDF locally; a changed PDF is drift, not a silent pass.</li>"
        )
        reproduce = (
            f"<h2>Reproduce one primary group</h2><pre><code>{esc(PRIMARY_VERIFY)}</code></pre>"
            "<p>Use the exact <code>runner_command</code> on each evidence card for the matching "
            "manifest path. Prefer card-level primary verifier guidance over Wikidata revision tools.</p>"
        )
    else:
        metrics = (
            f'<article class="metric"><strong>{primary_count:,} / 7,000</strong>primary-source statements</article>'
            f'<article class="metric"><strong>{wikidata_count:,} / 7,000</strong>Wikidata revision bindings</article>'
            '<article class="metric"><strong>100 / 100</strong>categories with exactly 70 claims</article>'
            f'<article class="metric"><strong>{reference_bound:,} / 7,000</strong>contain Wikidata reference blocks</article>'
            f'<article class="metric"><strong>{qualified:,} / 7,000</strong>contain Wikidata qualifiers</article>'
            '<article class="metric"><strong>0 / 7,000</strong>independent operator reruns</article>'
        )
        passed = (
            "<li>Primary cards bind exact quotes to official PDFs with dual-extractor checks.</li>"
            "<li>Wikidata cards bind distinct statements to immutable revisions and hashes.</li>"
            "<li>Raw source payloads are excluded; sanitized manifests and cards are committed.</li>"
            "<li>Every result states the narrow claim boundary and limitations.</li>"
        )
        limits = (
            "<li>Publication gates are not independent fact-checks.</li>"
            "<li>Wikidata reference blocks are counted but not followed as ground truth.</li>"
            "<li>No independent operator rerun is registered yet.</li>"
        )
        reproduce = (
            f"<h2>Reproduce one primary group</h2><pre><code>{esc(PRIMARY_VERIFY)}</code></pre>"
            "<h2>Reproduce one Wikidata card</h2>"
            f"<pre><code>{esc(WIKIDATA_VERIFY.format(claim_id='CB7K-DOM001-C01'))}</code></pre>"
        )
    return (
        "<p>CLAIMBOUND / HONESTY AND REPRODUCIBILITY AUDIT</p>"
        "<h1>Complete source bindings.<br>Limited evidentiary claim.</h1>"
        f'<section class="grid">{metrics}</section>'
        f"<h2>Passed checks</h2><ul>{passed}</ul>"
        f"<h2>Limitations and open verification gaps</h2><ul>{limits}</ul>"
        f'{reproduce}<p><a href="../results.json">Download all 7,000 detailed results</a></p>'
    )


def primary_claim_html(index: int, row: dict, card: dict, card_url: str) -> str:
    source_url = row["public_claim_source_url"]
    quote = row["public_claim_verbatim_quote"]
    command = card["runner_command"]
    return (
        f'''<article class="claim"><span class="tag">{esc(row['claim_id'])}</span>'''
        f'''<span class="tag">registry slot {esc(card['protocol_id'])}</span>'''
        '''<span class="tag pass">PASSED: EXACT PRIMARY-SOURCE STATEMENT FOUND</span>'''
        f'''<h2>{index}. {esc(card['official_source_name'])} · {esc(row['section_locator'])}</h2>'''
        '''<p class="muted">Narrow public claim</p>'''
        f'''<blockquote>{esc(row['public_claim_text'])}</blockquote>'''
        '''<h3>What this card proves</h3>'''
        f'''<p>The exact quoted statement occurred in the named official PDF fetched on '''
        f'''{esc(row['public_claim_captured_at'])}, and the complete PDF matched the recorded SHA-256.</p>'''
        '''<h3>What this card does not prove</h3>'''
        '''<p>It does not independently establish the underlying model capability, safety, '''
        '''comparison, or real-world truth. This is a retrospective single-maintainer '''
        '''source-publication audit.</p><dl>'''
        f'''<dt>Primary source</dt><dd><a href="{esc(source_url)}">{esc(card['official_source_name'])}</a></dd>'''
        f'''<dt>Section locator</dt><dd><code>{esc(row['section_locator'])}</code></dd>'''
        f'''<dt>Captured</dt><dd>{esc(row['public_claim_captured_at'])}</dd>'''
        f'''<dt>Source SHA-256</dt><dd><code>{esc(row['public_claim_source_sha256'])}</code></dd>'''
        '''<dt>Reproduction</dt><dd>Maintainer run only; no independent operator rerun is registered.</dd></dl>'''
        '''<details><summary>Repeat this exact check locally</summary>'''
        '''<p>Download the PDF to a local file, then run the committed verifier. '''
        '''A changed PDF is reported as drift rather than silently accepted.</p>'''
        f'''<pre><code>{esc(command)}</code></pre></details>'''
        '''<details><summary>Exact source quote</summary>'''
        f'''<blockquote><code>{esc(quote)}</code></blockquote>'''
        f'''<p class="links"><a href="{card_url}">Evidence card JSON</a>'''
        f'''<a href="{card_url[:-5]}.svg">Rendered card</a></p></details></article>'''
    )


def wikidata_claim_html(index: int, row: dict, card: dict, card_url: str) -> str:
    source_url = row["public_claim_source_url"]
    quote = row["public_claim_verbatim_quote"]
    command = WIKIDATA_VERIFY.format(claim_id=row["claim_id"])
    return (
        f'''<article class="claim"><span class="tag">{esc(row['claim_id'])}</span>'''
        f'''<span class="tag">registry slot {esc(card['protocol_id'])}</span>'''
        '''<span class="tag pass">PASSED: STATEMENT PUBLISHED IN REVISION</span>'''
        f'''<h2>{index}. {esc(row['entity_label'])} · {esc(row['property_label'])}</h2>'''
        '''<p class="muted">Exact public statement under test</p>'''
        f'''<blockquote>{esc(row['public_claim_text'])}</blockquote>'''
        '''<h3>What this card proves</h3>'''
        f'''<p>The exact statement GUID and JSON excerpt were publicly present in Wikidata '''
        f'''revision {row['revision_id']}; the frozen revision content and statement match '''
        '''the recorded SHA-256 values.</p>'''
        '''<h3>What this card does not prove</h3>'''
        '''<p>It does not independently prove that the value is true in the real world, '''
        '''current outside this revision, supported by a primary source, or correctly '''
        '''assigned to this category.</p><dl>'''
        f'''<dt>Exact source</dt><dd><a href="{esc(source_url)}">Wikidata revision {row['revision_id']}</a></dd>'''
        f'''<dt>Locator</dt><dd><code>{esc(row['public_claim_locator'])}</code></dd>'''
        f'''<dt>Captured</dt><dd>{esc(row['public_claim_captured_at'])}</dd>'''
        f'''<dt>Rank / qualifiers</dt><dd>{esc(row['wikidata_rank'])}; '''
        f'''{row['wikidata_qualifier_count']} qualifier snaks</dd>'''
        f'''<dt>Wikidata references</dt><dd>{row['wikidata_reference_count']} reference blocks — '''
        '''presence is reported, but the referenced sources were not independently checked '''
        '''by this protocol.</dd>'''
        f'''<dt>Source SHA-256</dt><dd><code>{esc(row['public_claim_source_sha256'])}</code></dd>'''
        f'''<dt>Statement SHA-256</dt><dd><code>{esc(row['statement_sha256'])}</code></dd>'''
        '''<dt>Reproduction</dt><dd>Maintainer run only; no independent operator rerun is registered.</dd></dl>'''
        '''<details><summary>Repeat this exact check locally</summary>'''
        '''<p>Requires Python 3 and network access to Wikidata. Start with an empty cache; '''
        '''the command downloads the immutable revision and verifies the exact excerpt and both hashes.</p>'''
        f'''<pre><code>{esc(command)}</code></pre></details>'''
        '''<details><summary>Verbatim structured statement and evidence</summary>'''
        f'''<blockquote><code>{esc(quote)}</code></blockquote>'''
        f'''<p class="links"><a href="{card_url}">Evidence card JSON</a>'''
        f'''<a href="{card_url[:-5]}.svg">Rendered card</a></p></details></article>'''
    )
