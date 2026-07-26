#!/usr/bin/env python3
"""Build the maintainer-published CB7K results atlas for GitHub Pages."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_public_claim_catalog import ROOT, domains, make_claims

CARD_RE = re.compile(r"CLAIMBOUND-(CB7K-DOM\d{3}-T\d{2}-G\d{2})-\d{4}-\d{2}-\d{2}\.json$")
REPO = "https://github.com/ClaimBound/claimbound-evidence"
STATUS_LABELS = {
    "PASSED_UNDER_PROTOCOL": "Passed under protocol",
    "INSUFFICIENT_COVERAGE": "Insufficient coverage",
    "NEGATIVE_RESULT_UNDER_PROTOCOL": "Negative result under protocol",
    "BLOCKED_SOURCE": "Blocked source",
    "SOURCE_DRIFT": "Source drift",
}


def esc(value: object) -> str:
    return html.escape(str(value or ""))


def load_cards() -> dict[str, tuple[Path, dict]]:
    found: dict[str, tuple[Path, dict]] = {}
    for path in sorted((ROOT / "docs/evidence_cards").glob("CLAIMBOUND-CB7K-*.json")):
        match = CARD_RE.search(path.name)
        if not match:
            continue
        protocol_id = match.group(1)
        if protocol_id in found:
            raise SystemExit(f"ERROR: duplicate evidence card for {protocol_id}")
        found[protocol_id] = (path, json.loads(path.read_text(encoding="utf-8")))
    if len(found) != 7000:
        raise SystemExit(f"ERROR: expected 7000 CB7K cards, got {len(found)}")
    return found


def batch_issue(domain_number: int) -> int:
    return 166 + (domain_number - 1) // 3


def page(title: str, body: str, root: str = "") -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="ClaimBound CB7K evidence-card results published by the maintainer"><title>{esc(title)} · ClaimBound CB7K</title><style>
:root{{--ink:#172d31;--muted:#607276;--paper:#f3efe5;--card:#fffdf8;--line:#c9c2b4;--accent:#006d68;--pass:#217a55;--insufficient:#9a6500;--negative:#a33c35;--blocked:#675d8c;--drift:#9b4f78}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1240px;margin:auto;padding:30px 22px 80px}}a{{color:var(--accent)}}nav{{display:flex;gap:18px;flex-wrap:wrap}}h1,h2{{font-family:Georgia,serif}}h1{{font-size:clamp(36px,6vw,68px);line-height:1;max-width:1000px;margin:.45em 0}}h2{{line-height:1.15}}.lede{{font-size:19px;max-width:850px}}.note,.claim,.domain,.metric{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.claims{{display:grid;gap:14px;margin-top:18px}}.claim h2{{margin:.55em 0 .25em}}.metric strong{{font:700 30px Georgia,serif;display:block}}.tag{{display:inline-block;padding:4px 9px;border-radius:99px;background:#e3ece8;margin:0 6px 6px 0;font-size:13px}}.status{{color:white}}.PASSED_UNDER_PROTOCOL{{background:var(--pass)}}.INSUFFICIENT_COVERAGE{{background:var(--insufficient)}}.NEGATIVE_RESULT_UNDER_PROTOCOL{{background:var(--negative)}}.BLOCKED_SOURCE{{background:var(--blocked)}}.SOURCE_DRIFT{{background:var(--drift)}}small,.muted{{color:var(--muted)}}blockquote{{margin-left:0;border-left:4px solid var(--accent);padding-left:14px}}input,select{{padding:12px;border:1px solid var(--line);border-radius:9px;font:inherit;background:white}}input{{width:min(100%,520px)}}.filters{{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}}.links{{display:flex;gap:14px;flex-wrap:wrap}}[hidden]{{display:none}}code{{overflow-wrap:anywhere}}details{{margin-top:10px}}summary{{cursor:pointer;font-weight:650}}
</style></head><body><main><nav><a href="{root}index.html">All categories</a><a href="{REPO}/issues/165">Campaign issue #165</a><a href="{REPO}">Repository</a></nav>{body}</main></body></html>'''


def build(output: Path) -> None:
    ds = domains()
    candidates = {c["claim_id"]: c for c in make_claims(ds)}
    cards = load_cards()
    if set(cards) != set(candidates):
        missing = sorted(set(candidates) - set(cards))
        extra = sorted(set(cards) - set(candidates))
        raise SystemExit(f"ERROR: card/catalog mismatch; missing={missing[:3]} extra={extra[:3]}")
    if output.exists():
        shutil.rmtree(output)
    (output / "categories").mkdir(parents=True)
    all_counts: Counter[str] = Counter()
    category_tiles: list[str] = []
    results: list[dict] = []
    for number, domain in enumerate(ds, 1):
        code = f"DOM{number:03d}"
        category_claims = [c for c in candidates.values() if c["domain_code"] == code]
        counts: Counter[str] = Counter()
        claim_html: list[str] = []
        for candidate in category_claims:
            path, card = cards[candidate["claim_id"]]
            status = card.get("result_status", "UNKNOWN")
            if status not in STATUS_LABELS:
                raise SystemExit(f"ERROR: {candidate['claim_id']} unknown status {status}")
            counts[status] += 1
            all_counts[status] += 1
            json_url = f"{REPO}/blob/main/{path.relative_to(ROOT).as_posix()}"
            svg_path = path.with_suffix(".svg")
            svg_url = f"{REPO}/blob/main/{svg_path.relative_to(ROOT).as_posix()}"
            searchable = esc(" ".join([candidate["claim_id"], candidate["topic"], candidate["gate"], status, candidate["frozen_candidate_claim"]]).lower())
            claim_html.append(f'''<article class="claim" data-search="{searchable}" data-status="{esc(status)}"><span class="tag">{esc(candidate['claim_id'])}</span><span class="tag">{esc(candidate['gate'])}</span><span class="tag status {esc(status)}">{esc(STATUS_LABELS[status])}</span><h2>{esc(candidate['topic'])}</h2><blockquote>{esc(candidate['frozen_candidate_claim'])}</blockquote><p><strong>Result boundary:</strong> {esc(card.get('claim_boundary'))}</p><p><strong>Maintainer review:</strong> {esc(card.get('manual_review'))}</p><details><summary>Source and reproducibility details</summary><p><strong>Official source:</strong> <a href="{esc(card.get('official_source_url'))}">{esc(card.get('official_source_name'))}</a></p><p><strong>Reproduction:</strong> {esc(card.get('reproduction_level'))}; <strong>verification:</strong> {esc(card.get('verification_level'))} ({esc(card.get('verification_count'))})</p><p><strong>Limitations:</strong> {esc('; '.join(card.get('known_limitations', [])))}</p><p class="links"><a href="{json_url}">Evidence JSON</a><a href="{svg_url}">Rendered card</a></p></details></article>''')
            results.append({"claim_id": candidate["claim_id"], "category": domain["slug"], "topic": candidate["topic"], "gate": candidate["gate"], "claim": candidate["frozen_candidate_claim"], "result_status": status, "claim_boundary": card.get("claim_boundary"), "manual_review": card.get("manual_review"), "official_source_name": card.get("official_source_name"), "official_source_url": card.get("official_source_url"), "evidence_card": path.relative_to(ROOT).as_posix()})
        issue = batch_issue(number)
        summary = "".join(f'<div class="metric"><strong>{counts.get(status,0)}</strong><span>{esc(label)}</span></div>' for status, label in STATUS_LABELS.items())
        category_body = f'''<p>CLAIMBOUND / VERIFIED CATEGORY {code}</p><h1>{esc(domain['title'])}</h1><p class="lede">70 preregistered claims across seven topics and ten evidence gates. Results are claim-scoped findings, not certification of this category.</p><p><a href="{REPO}/issues/{issue}">Batch issue #{issue}</a> · Maintainer: NeoZorK · Single-operator publication</p><section class="grid">{summary}</section><div class="filters"><input id="q" type="search" placeholder="Search claims, topics, and gates" aria-label="Search claims"><select id="status" aria-label="Filter by result"><option value="">All results</option>{''.join(f'<option value="{s}">{esc(l)}</option>' for s,l in STATUS_LABELS.items())}</select></div><section class="claims">{''.join(claim_html)}</section><script>const q=document.querySelector('#q'),s=document.querySelector('#status'),items=[...document.querySelectorAll('.claim')];function filter(){{const text=q.value.toLowerCase();items.forEach(x=>x.hidden=!(x.dataset.search.includes(text)&&(!s.value||x.dataset.status===s.value)))}}q.oninput=filter;s.onchange=filter;</script>'''
        category_dir = output / "categories" / domain["slug"]
        category_dir.mkdir()
        (category_dir / "index.html").write_text(page(domain["title"], category_body, "../../"), encoding="utf-8")
        count_text = " · ".join(f"{counts.get(s,0)} {l.lower()}" for s,l in STATUS_LABELS.items() if counts.get(s))
        category_tiles.append(f'<article class="domain" data-search="{esc((domain["title"]+" "+domain["slug"]+" "+" ".join(domain["topics"])).lower())}"><p><small>{code} · issue #{issue}</small></p><h2><a href="categories/{esc(domain['slug'])}/">{esc(domain['title'])}</a></h2><p>70 claims · {esc(count_text)}</p></article>')
    metrics = "".join(f'<div class="metric"><strong>{all_counts.get(status,0)}</strong><span>{esc(label)}</span></div>' for status,label in STATUS_LABELS.items())
    home = f'''<p>CLAIMBOUND / MAINTAINER-PUBLISHED RESULTS</p><h1>7,000 claim checks.<br>100 category reports.</h1><p class="lede">The completed results of issues #165–#199, published from the validated evidence-card registry. Each category has its own stable URL and all 70 claim-level outcomes.</p><div class="note"><strong>Interpretation boundary.</strong> A pass supports only the narrow claim under its frozen protocol. Non-pass results are retained. Nothing here certifies an institution, product, policy, source, or whole category.</div><section class="grid" style="margin:18px 0">{metrics}</section><p class="links"><a href="results.json">Download all results (JSON)</a><a href="{REPO}/issues/165">Master issue #165</a></p><div class="filters"><input id="q" type="search" placeholder="Filter 100 categories" aria-label="Filter categories"></div><section class="grid">{''.join(category_tiles)}</section><script>const q=document.querySelector('#q');q.oninput=()=>document.querySelectorAll('.domain').forEach(x=>x.hidden=!x.dataset.search.includes(q.value.toLowerCase()))</script>'''
    (output / "index.html").write_text(page("7,000 verified public claims", home), encoding="utf-8")
    (output / "results.json").write_text(json.dumps({"maintainer":"NeoZorK","campaign_issue":165,"category_count":100,"claim_count":7000,"result_counts":all_counts,"results":results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(results)} results across {len(ds)} category pages: {dict(all_counts)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("tmp/verified-claim-atlas"))
    args = parser.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
