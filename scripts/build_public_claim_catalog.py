#!/usr/bin/env python3
"""Build a 7,000-candidate ClaimBound backlog and domain-separated static atlas."""
from __future__ import annotations
import argparse, hashlib, html, json, shutil, subprocess, tempfile, urllib.parse
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DATA_DIR=ROOT/'docs/public_claims/domains'
VERSION='2026-07-16-v1'; N_DOMAINS=100; PER_DOMAIN=70; N_CLAIMS=7000; BATCH_DOMAINS=3
OUTCOMES=['PASSED_UNDER_PROTOCOL','INSUFFICIENT_COVERAGE','NEGATIVE_RESULT_UNDER_PROTOCOL','BLOCKED_SOURCE','SOURCE_DRIFT']
GATES=[
('source-integrity','The headline about {topic} can be traced to one exact public source version, canonical URL, access time, redirect chain, and SHA-256 hash.','Freeze the exact source before the first fetch; do not replace a blocked or weak source after seeing the result.'),
('numerator-denominator','The published number for {topic} reproduces from the disclosed numerator, denominator, units, exclusions, and rounding rule.','A nearby number or a recalculation with a different denominator is insufficient.'),
('coverage','The public claim about {topic} does not silently exclude affected people, places, incidents, products, time periods, or failed cases.','Record the population, geography, inclusion rules, missingness, and known coverage limits.'),
('time-boundary','The public claim about {topic} is valid for the stated date or period and is not inherited from an older page, dataset, label, model, or policy version.','Historical and current claims require separate cards; later drift must not rewrite the baseline.'),
('method-version','The claimed performance or change in {topic} survives the exact disclosed method, software version, thresholds, transformations, and quality controls.','Freeze the method before execution and preserve version or implementation drift.'),
('comparator','The comparison behind {topic} uses a genuinely comparable baseline, population, operating condition, time window, and measurement rule.','Do not compare unlike populations, definitions, roads, hospitals, models, years, products, or geographies.'),
('reproducibility','An independent operator can obtain the same public inputs for {topic} and rerun the frozen protocol without private credentials or undisclosed data.','If access, licensing, paywalls, robots rules, missing files, or private inputs prevent this, preserve BLOCKED_SOURCE.'),
('negative-evidence','Negative, failed, delayed, recalled, blocked, adverse, or contradictory evidence relevant to {topic} is not omitted from the selected boundary.','Absence alone is not a negative result; record INSUFFICIENT_COVERAGE unless the frozen protocol establishes contradiction.'),
('conflicts-disclosure','Sponsor, vendor, author, ownership, procurement, or institutional interests relevant to {topic} are disclosed inside the audit boundary.','Disclosure is not proof of bias; missing disclosure is not proof of misconduct.'),
('overclaim-drift','The selected source does not justify a broader promise that {topic} is universally safe, effective, complete, causal, permanent, certified, or guaranteed.','A pass is only source support for the narrow wording. It is never domain-wide certification or endorsement.'),
]

def domains()->list[dict[str,Any]]:
    data=[]
    for path in sorted(DATA_DIR.glob('domain_catalog_*.json')):
        part=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(part,list): raise SystemExit(f'ERROR: {path} must contain a list')
        data.extend(part)
    if not data: raise SystemExit('ERROR: no domain catalog chunks found')
    return data

def make_claims(ds:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]; ordinal=0
    for di,d in enumerate(ds,1):
        code=f'DOM{di:03d}'
        for ti,topic in enumerate(d['topics'],1):
            for gi,(gate,template,rule) in enumerate(GATES,1):
                ordinal+=1
                out.append({'catalog_version':VERSION,'ordinal':ordinal,'claim_id':f'CB7K-{code}-T{ti:02d}-G{gi:02d}','domain_code':code,'domain_slug':d['slug'],'domain_title':d['title'],'topic_index':ti,'topic':topic,'gate_index':gi,'gate':gate,'frozen_candidate_claim':template.format(topic=topic),'adjudication_rule':rule,'suggested_source_boundary':d['source_hint'],'source_url':None,'source_frozen_sha256':None,'status':'PENDING_SOURCE_SELECTION','honest_outcomes':OUTCOMES,'raw_payload_committed':False})
    return out

def validate(ds:list[dict[str,Any]],claims:list[dict[str,Any]])->None:
    errors=[]
    if len(ds)!=N_DOMAINS: errors.append(f'expected {N_DOMAINS} domains, got {len(ds)}')
    if len(claims)!=N_CLAIMS: errors.append(f'expected {N_CLAIMS} claims, got {len(claims)}')
    ids=[x['claim_id'] for x in claims]
    if len(ids)!=len(set(ids)): errors.append('claim IDs are not unique')
    slugs=[d['slug'] for d in ds]
    if len(slugs)!=len(set(slugs)): errors.append('domain slugs are not unique')
    for d in ds:
        if len(d.get('topics',[]))!=7: errors.append(f"{d.get('slug')}: expected 7 topics")
    counts={s:0 for s in slugs}
    for c in claims:
        counts[c['domain_slug']]+=1
        if c['status']!='PENDING_SOURCE_SELECTION': errors.append(f"{c['claim_id']}: bad initial status")
        if c['source_url'] is not None: errors.append(f"{c['claim_id']}: source preselected")
        if c['raw_payload_committed'] is not False: errors.append(f"{c['claim_id']}: raw payload policy")
    bad={s:n for s,n in counts.items() if n!=PER_DOMAIN}
    if bad: errors.append(f'domain counts: {bad}')
    if errors: raise SystemExit('\n'.join('ERROR: '+x for x in errors))

def issue_url(c:dict[str,Any])->str:
    body=(f"Candidate ID: `{c['claim_id']}`\n\nDomain: **{c['domain_title']}**\n\nFrozen candidate claim:\n\n> {c['frozen_candidate_claim']}\n\nBefore the first network fetch, add one exact canonical public source URL and record the frozen source-manifest SHA-256.\n\nHonest outcomes: `PASSED_UNDER_PROTOCOL`, `INSUFFICIENT_COVERAGE`, `NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE`, or `SOURCE_DRIFT`.\n")
    return 'https://github.com/ClaimBound/claimbound-evidence/issues/new?'+urllib.parse.urlencode({'title':f"Verify {c['claim_id']}: {c['topic']}",'body':body})

def shell(title:str,body:str,root:str='')->str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · ClaimBound</title><style>:root{{--ink:#17383a;--paper:#f5f0e4;--card:#fffdf7;--line:#b9b4a7;--accent:#165b5c}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:34px 22px 70px}}a{{color:var(--accent)}}h1,h2{{font-family:Georgia,serif}}h1{{font-size:clamp(34px,6vw,62px);line-height:1.02}}.note,.claim,.domain{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}}.tag{{display:inline-block;padding:3px 8px;border-radius:99px;background:#e6f0eb;margin-right:6px;font-size:13px}}small{{color:#5f6f6f}}code{{overflow-wrap:anywhere}}input{{width:100%;padding:13px;border:1px solid var(--line);border-radius:10px;font:inherit}}[hidden]{{display:none}}blockquote{{margin-left:0;border-left:4px solid var(--accent);padding-left:14px}}nav a{{margin-right:16px}}</style></head><body><main><nav><a href="{root}index.html">Claim catalog home</a><a href="https://github.com/ClaimBound/claimbound-evidence">Repository</a></nav>{body}</main></body></html>'''

def build(output:Path,ds:list[dict[str,Any]],claims:list[dict[str,Any]])->None:
    if output.exists(): shutil.rmtree(output)
    (output/'domains').mkdir(parents=True); (output/'issues').mkdir()
    catalog={'catalog_version':VERSION,'domain_count':len(ds),'claim_count':len(claims),'claims_per_domain':PER_DOMAIN,'initial_status':'PENDING_SOURCE_SELECTION','honest_outcomes':OUTCOMES,'domains':ds,'claims':claims}
    (output/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'catalog.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in claims),encoding='utf-8')
    cards=[]
    for d in ds:
        dc=[c for c in claims if c['domain_slug']==d['slug']]; p=output/'domains'/d['slug']; p.mkdir()
        search=html.escape((d['title']+' '+d['slug']+' '+' '.join(d['topics'])).lower())
        cards.append(f'<article class="domain" data-search="{search}"><h2><a href="domains/{d["slug"]}/">{html.escape(d["title"])}</a></h2><p>70 candidates · 7 topics · 10 gates</p><small>{html.escape(d["source_hint"])}</small></article>')
        blocks=[]
        for c in dc:
            s=html.escape((c['claim_id']+' '+c['topic']+' '+c['gate']).lower())
            blocks.append(f'<article class="claim" data-search="{s}"><span class="tag">{c["claim_id"]}</span><span class="tag">{html.escape(c["gate"])}</span><h2>{html.escape(c["topic"])}</h2><blockquote>{html.escape(c["frozen_candidate_claim"])}</blockquote><p><strong>Before fetch:</strong> {html.escape(c["adjudication_rule"])}</p><p><a href="{html.escape(issue_url(c),quote=True)}">Open one verification issue</a></p></article>')
        body=f'<p>CLAIMBOUND / DOMAIN CANDIDATES</p><h1>{html.escape(d["title"])}</h1><div class="note"><strong>70 pending candidates, not evidence.</strong> Initial status: <code>PENDING_SOURCE_SELECTION</code>. Suggested source boundary: {html.escape(d["source_hint"])}. Freeze one exact URL before network access and keep every honest non-pass.</div><input id="q" placeholder="Filter 70 candidates">'+''.join(blocks)+"<script>const q=document.querySelector('#q');q.oninput=()=>document.querySelectorAll('.claim').forEach(x=>x.hidden=!x.dataset.search.includes(q.value.toLowerCase()))</script>"
        (p/'index.html').write_text(shell(d['title'],body,'../../'),encoding='utf-8')
    home='<p>CLAIMBOUND / PUBLIC CLAIM CANDIDATE ATLAS</p><h1>7,000 claims across 100 domains</h1><div class="note"><strong>This is a preregistered backlog, not evidence.</strong> Every candidate begins at <code>PENDING_SOURCE_SELECTION</code>. Freeze one exact source before fetching; preserve PASS, INSUFFICIENT, NEGATIVE, BLOCKED, or DRIFT without rewriting.</div><p><a href="catalog.json">JSON</a> · <a href="catalog.jsonl">JSONL</a> · <a href="issues/">Issue-ready batches</a></p><input id="q" placeholder="Filter 100 domains"><section class="grid">'+''.join(cards)+"</section><script>const q=document.querySelector('#q');q.oninput=()=>document.querySelectorAll('.domain').forEach(x=>x.hidden=!x.dataset.search.includes(q.value.toLowerCase()))</script>"
    (output/'index.html').write_text(shell('7,000 public claim candidates',home),encoding='utf-8')
    batches=[ds[i:i+BATCH_DOMAINS] for i in range(0,len(ds),BATCH_DOMAINS)]; idx=['# Issue-ready candidate batches','','> Candidate backlog only; no result is predeclared.','']
    for bi,bds in enumerate(batches,1):
        slugs={d['slug'] for d in bds}; bc=[c for c in claims if c['domain_slug'] in slugs]; name=f'batch-{bi:02d}.md'
        idx.append(f"- [Batch {bi:02d}]({name}) — {', '.join(d['title'] for d in bds)} ({len(bc)} candidates)")
        lines=[f'# Public claim catalog batch {bi:02d}/{len(batches):02d}','',f'**Scope:** {len(bds)} domains × 70 candidates = {len(bc)} locally verifiable candidate claims.','', '> [!IMPORTANT]','> These are frozen candidate questions, not evidence. Every entry starts at `PENDING_SOURCE_SELECTION`.','> Freeze one exact public source URL before the first network fetch. Never replace a blocked or weak source after seeing the result.','', 'Honest outcomes: `PASSED_UNDER_PROTOCOL`, `INSUFFICIENT_COVERAGE`, `NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE`, `SOURCE_DRIFT`.','', '## Local preparation','', '```bash','python3 scripts/build_public_claim_catalog.py validate','python3 scripts/build_public_claim_catalog.py build --output tmp/public-claim-catalog',f'cat tmp/public-claim-catalog/issues/{name}','```','']
        for d in bds:
            lines += [f"## {d['title']} — `{d['slug']}`",'',f"Suggested source boundary: {d['source_hint']}.",'']
            for c in (x for x in bc if x['domain_slug']==d['slug']): lines.append(f"- [ ] `{c['claim_id']}` — **{c['topic']} / {c['gate']}** — {c['frozen_candidate_claim']}")
            lines.append('')
        lines += ['## Honest completion gate','','- [ ] Exact source URL selected and frozen before fetch for each executed candidate.','- [ ] Canonical URL, redirects, access time, HTTP result, and SHA-256 recorded.','- [ ] No source widening or claim rewriting after observing the result.','- [ ] Every non-pass reviewed and retained.','- [ ] Raw source payload remains local.','- [ ] Published evidence cards pass `uv run claimbound validate-all` and tests.','']
        (output/'issues'/name).write_text('\n'.join(lines),encoding='utf-8')
    (output/'issues'/'README.md').write_text('\n'.join(idx)+'\n',encoding='utf-8')
    links=''.join(f'<article class="domain"><h2><a href="batch-{i:02d}.md">Batch {i:02d}</a></h2><p>{len(b)} domains · {len(b)*PER_DOMAIN} candidates</p></article>' for i,b in enumerate(batches,1))
    (output/'issues'/'index.html').write_text(shell('Issue-ready batches',f'<p>CLAIMBOUND / ISSUE-READY BACKLOG</p><h1>{len(batches)} batches</h1><div class="note">Each batch contains up to 210 candidates and fits one GitHub issue.</div><section class="grid">{links}</section>','../'),encoding='utf-8')

def freeze(path:Path)->None:
    payload=json.loads(path.read_text(encoding='utf-8')); sources=payload.get('sources')
    if not isinstance(sources,list) or not sources: raise SystemExit("ERROR: manifest needs non-empty 'sources'")
    for i,x in enumerate(sources,1):
        u=x.get('source_url')
        if not isinstance(u,str) or not u.startswith(('https://','http://')) or 'TODO' in u.upper() or 'FILL' in u.upper(): raise SystemExit(f'ERROR: invalid source #{i}')
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); print(hashlib.sha256(raw).hexdigest())

def run_build(out:Path)->None:
    ds=domains(); cs=make_claims(ds); validate(ds,cs); build(out,ds,cs)

def command_validate()->None:
    ds=domains(); cs=make_claims(ds); validate(ds,cs)
    with tempfile.TemporaryDirectory() as t:
        out=Path(t)/'site'; build(out,ds,cs)
        if len(list((out/'domains').glob('*/index.html')))!=N_DOMAINS: raise SystemExit('ERROR: domain page count')
        batches=list((out/'issues').glob('batch-*.md'))
        if len(batches)!=34 or max(x.stat().st_size for x in batches)>=65536: raise SystemExit('ERROR: issue batches')
        if json.loads((out/'catalog.json').read_text())['claim_count']!=N_CLAIMS: raise SystemExit('ERROR: catalog count')
    print('OK: 7000 unique candidates, 100 domain pages, 34 issue batches')

def publish(out:Path,repo:str,execute:bool)->None:
    run_build(out); files=sorted((out/'issues').glob('batch-*.md'))
    if not execute:
        print(f'DRY RUN: would create {len(files)} issues in {repo}'); [print(x) for x in files]; return
    if shutil.which('gh') is None: raise SystemExit("ERROR: gh required; run 'gh auth status'")
    subprocess.run(['gh','auth','status'],check=True)
    for i,f in enumerate(files,1): subprocess.run(['gh','issue','create','--repo',repo,'--title',f'Public claim catalog batch {i:02d}/{len(files):02d}: candidate domains','--body-file',str(f)],check=True)

def main()->int:
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
    b=s.add_parser('build'); b.add_argument('--output',type=Path,default=Path('tmp/public-claim-catalog'))
    s.add_parser('validate'); f=s.add_parser('freeze-manifest'); f.add_argument('manifest',type=Path)
    u=s.add_parser('publish-issues'); u.add_argument('--output',type=Path,default=Path('tmp/public-claim-catalog')); u.add_argument('--repo',default='ClaimBound/claimbound-evidence'); u.add_argument('--publish',action='store_true')
    a=p.parse_args()
    if a.cmd=='build': run_build(a.output); print(f'Built 7000 candidates across 100 domains at {a.output}')
    elif a.cmd=='validate': command_validate()
    elif a.cmd=='freeze-manifest': freeze(a.manifest)
    else: publish(a.output,a.repo,a.publish)
    return 0
if __name__=='__main__': raise SystemExit(main())
