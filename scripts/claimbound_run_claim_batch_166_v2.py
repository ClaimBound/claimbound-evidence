#!/usr/bin/env python3
"""Execute issue #166 with topic-frozen sources and gate-specific rules."""
from __future__ import annotations

import argparse, hashlib, html, json, re, urllib.error, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_public_claim_catalog import GATE_METHODS, domains, make_claims, validate, validate_execution_manifest
from claimbound_evidence.card_svg_render import render_svg
from claimbound_evidence.evidence_card import validate_evidence_card

ROOT=Path(__file__).resolve().parents[1]
CARDS=ROOT/'docs/evidence_cards'; REGISTRY=ROOT/'docs/registry/evidence_index.json'
MANIFEST=ROOT/'artifacts/claim_batch_166_execution_manifest.json'
REPORT=ROOT/'artifacts/claim_batch_166_v2_summary.json'
PROTOCOL='CB7K-ISSUE-166-CLAIM-LEVEL-2026-07-20-v2'

SOURCES={
('DOM001',1):('OpenAI GPT-5.6 System Card','https://deploymentsafety.openai.com/gpt-5-6'),
('DOM001',2):('OpenAI GPT-5.5 System Card','https://deploymentsafety.openai.com/gpt-5-5'),
('DOM001',3):('OpenAI GPT-4.1 release','https://openai.com/index/gpt-4-1/'),
('DOM001',4):('OpenAI API pricing','https://openai.com/api/pricing/'),
('DOM001',5):('Google sustainability reports','https://sustainability.google/reports/'),
('DOM001',6):('OpenAI GPT-5.6 safeguards','https://deploymentsafety.openai.com/gpt-5-6/safeguards'),
('DOM001',7):('OpenAI Operator System Card','https://openai.com/index/operator-system-card/'),
('DOM002',1):('Stanford CRFM HELM Classic','https://crfm.stanford.edu/helm/latest/'),
('DOM002',2):('Stanford CRFM HELM Lite','https://crfm.stanford.edu/helm/lite/latest/'),
('DOM002',3):('Stanford CRFM HELM MMLU','https://crfm.stanford.edu/helm/mmlu/latest/'),
('DOM002',4):('Stanford CRFM VHELM','https://crfm.stanford.edu/helm/vhelm/v2.0.0/'),
('DOM002',5):('Stanford CRFM HEIM','https://crfm.stanford.edu/helm/heim/latest/'),
('DOM002',6):('Stanford CRFM AIR-Bench','https://crfm.stanford.edu/helm/air-bench/latest/'),
('DOM002',7):('Stanford CRFM HELM Safety','https://crfm.stanford.edu/helm/safety/latest/'),
('DOM003',1):('OpenAI GPT-5.6 System Card','https://deploymentsafety.openai.com/gpt-5-6'),
('DOM003',2):('OpenAI Operator System Card','https://openai.com/index/operator-system-card/'),
('DOM003',3):('OpenAI GPT-5 biological risk evaluation','https://deploymentsafety.openai.com/gpt-5/long-form-biological-risk-questions'),
('DOM003',4):('OpenAI GPT-5 cybersecurity evaluation','https://deploymentsafety.openai.com/gpt-5/cybersecurity'),
('DOM003',5):('OpenAI ChatGPT Agent System Card','https://cdn.openai.com/pdf/839e66fc-602c-48bf-81d3-b21eacc3459d/chatgpt_agent_system_card.pdf'),
('DOM003',6):('OpenAI o3 and o4-mini System Card','https://deploymentsafety.openai.com/o3/appendix'),
('DOM003',7):('OpenAI GPT-5.5 safeguards','https://deploymentsafety.openai.com/gpt-5-5/safeguards'),
}

RULES={
'source-integrity':({'required':['http_2xx','sha256','canonical_url']},'retrieval succeeds and source identity fields are recorded','retrieval is blocked or source identity cannot be fixed'),
'numerator-denominator':({'all_terms':['numerator','denominator'],'numeric_token':True},'source explicitly discloses numerator and denominator with a numeric result','an explicit disclosed recomputation contradicts the published result'),
'coverage':({'any_terms':['coverage','limitations','scope','dataset']},'source explicitly states a coverage, scope, dataset, or limitations boundary','source explicitly claims complete coverage while documenting an exclusion'),
'time-boundary':({'any_terms':['version','updated','published','release']},'source exposes a version, publication, update, or release boundary','source explicitly assigns the result to a conflicting version or period'),
'method-version':({'all_groups':[['method','evaluation'],['version','v1','v2','2024','2025','2026']]},'source identifies an evaluation or method and a version marker','a disclosed rerun under the exact method contradicts the claim'),
'comparator':({'any_terms':['baseline','compare','comparison','versus',' vs ']},'source explicitly identifies a baseline or comparison','source states that the compared populations or methods are not comparable'),
'reproducibility':({'required':['stable_refetch']},'two independent public retrievals return identical bytes','the second public retrieval returns conflicting bytes under the frozen URL'),
'negative-evidence':({'any_terms':['failure','failed','risk','limitation','incident','harm','adverse']},'source explicitly includes adverse, failed, risk, limitation, incident, or harm evidence','source explicitly asserts absence of the preregistered adverse event under a disclosed complete register'),
'conflicts-disclosure':({'any_terms':['acknowledg','author','contributor','sponsor','financial support','disclosure']},'source includes authorship, contributors, sponsors, financial support, or disclosure information','an explicit disclosure contradicts the frozen statement'),
'overclaim-drift':({'any_terms':['limitation','may not','does not guarantee','scope','risk']},'source contains an explicit limitation or scope caveat and no universal certification is inferred','source itself explicitly makes and then retracts a universal guarantee'),
}

def manifest(claims:list[dict[str,Any]])->dict[str,Any]:
    entries=[]
    for c in claims:
        name,url=SOURCES[(c['domain_code'],c['topic_index'])]; params,support,negative=RULES[c['gate']]
        entries.append({'claim_id':c['claim_id'],'source_name':name,'source_url':url,'evaluation_method':GATE_METHODS[c['gate']],
                        'frozen_parameters':params,'support_rule':support,'negative_rule':negative})
    return {'issue_number':166,'protocol_version':PROTOCOL,'claim_boundary':'Claim-level execution plan for issue #166 only; it is not evidence and predeclares no outcome.','frozen_before_fetch':True,'entries':entries}

def fetch(url:str, raw_path:Path|None=None)->dict[str,Any]:
    req=urllib.request.Request(url,headers={'User-Agent':'ClaimBound/1.0 (+https://github.com/ClaimBound/claimbound-evidence)'})
    try:
        with urllib.request.urlopen(req,timeout=60) as r: body,status,final,ctype=r.read(),r.status,r.geturl(),r.headers.get('Content-Type','')
    except urllib.error.HTTPError as e: body,status,final,ctype=e.read(),e.code,e.geturl(),e.headers.get('Content-Type','')
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return {'http_status':None,'canonical_url':None,'content_type':None,'sha256':None,'text':'','error':f'{type(e).__name__}: {e}','stable_refetch':False}
    if raw_path is not None:
        raw_path.parent.mkdir(parents=True,exist_ok=True); raw_path.write_bytes(body)
    text=body.decode('utf-8','replace') if 'pdf' not in ctype.lower() else ''
    text=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',text))).lower()
    return {'http_status':status,'canonical_url':final,'content_type':ctype,'sha256':hashlib.sha256(body).hexdigest(),'text':text,'error':None,'stable_refetch':False}

def supported(claim:dict[str,Any], source:dict[str,Any])->tuple[bool,list[str]]:
    gate=claim['gate']
    p=RULES[gate][0]; text=source['text']; observed=[]
    topic_terms=[x for x in re.findall(r'[a-z][a-z-]{3,}',claim['topic'].lower()) if x not in {'claim','rate'}]
    topic_found=[x for x in topic_terms if x in text]
    checks=[bool(topic_found)]; observed.append('topic_anchor='+','.join(topic_found))
    for required in p.get('required',[]):
        ok={'http_2xx':isinstance(source['http_status'],int) and 200<=source['http_status']<300,
            'sha256':bool(source['sha256']),'canonical_url':bool(source['canonical_url']),
            'stable_refetch':source['stable_refetch']}[required]
        checks.append(ok); observed.append(f'{required}={ok}')
    if 'all_terms' in p:
        found=[x for x in p['all_terms'] if x in text]; checks.append(len(found)==len(p['all_terms'])); observed.append('all_terms='+','.join(found))
    if p.get('numeric_token'):
        ok=bool(re.search(r'\b\d+(?:\.\d+)?%?\b',text)); checks.append(ok); observed.append(f'numeric_token={ok}')
    if 'any_terms' in p:
        found=[x for x in p['any_terms'] if x in text]; checks.append(bool(found)); observed.append('any_terms='+','.join(found))
    for group in p.get('all_groups',[]):
        found=[x for x in group if x in text]; checks.append(bool(found)); observed.append('group='+','.join(found))
    return all(checks),observed

def registry_entry(card:dict[str,Any],path:Path)->dict[str,Any]:
    keys=('evidence_id','registry_sequence','result_status','protocol_id','domain','record_type','operator','created_at','last_verified_date','verification_level','verification_count','reproduction_level','official_source_name','sanitized_report_path')
    return {k:card[k] for k in keys}|{'path':str(path.relative_to(ROOT))}

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('command',choices=['preview','publish']); ap.add_argument('--operator',required=True); args=ap.parse_args()
    ds=domains(); all_claims=make_claims(ds); validate(ds,all_claims); claims=[c for c in all_claims if c['domain_code'] in {'DOM001','DOM002','DOM003'}]
    payload=manifest(claims); MANIFEST.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n'); validate_execution_manifest(MANIFEST)
    manifest_sha=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(); accessed=datetime.now(timezone.utc); date=accessed.date().isoformat()
    run_root=Path('/private/tmp')/f"CLAIM_BATCH_166_V2_{accessed.strftime('%Y%m%dT%H%M%SZ')}"; raw_dir=run_root/'raw'
    fetched={}
    for key,(_,url) in SOURCES.items(): fetched[key]=fetch(url,raw_dir/f'{key[0]}-T{key[1]:02d}.bin')
    for key,(_,url) in SOURCES.items():
        second=fetch(url); fetched[key]['stable_refetch']=bool(fetched[key]['sha256'] and fetched[key]['sha256']==second['sha256'])
    rows=[]
    for c,e in zip(claims,payload['entries']):
        source=fetched[(c['domain_code'],c['topic_index'])]
        if not isinstance(source['http_status'],int) or not 200<=source['http_status']<300: status='BLOCKED_SOURCE'; observed=[source['error'] or f"HTTP {source['http_status']}"]
        else:
            ok,observed=supported(c,source); status='PASSED_UNDER_PROTOCOL' if ok else 'INSUFFICIENT_COVERAGE'
        rows.append({**c,**e,'result_status':status,'observed_checks':observed,**{k:v for k,v in source.items() if k!='text'}})
    report={'issue_number':166,'protocol_version':PROTOCOL,'claim_boundary':'210 frozen candidate claims from DOM001-DOM003; each outcome is limited to one topic source and one gate-specific rule. No domain-wide certification.','accessed_at':accessed.isoformat(),'operator':args.operator,'execution_manifest_sha256':manifest_sha,
            'claim_level_entries':len(rows),'unique_frozen_urls':len({r['source_url'] for r in rows}),'local_raw_payload_retained':True,'raw_payload_committed':False,
            'result_counts':dict(Counter(r['result_status'] for r in rows)),'cards':rows}
    REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); report_sha=hashlib.sha256(REPORT.read_bytes()).hexdigest()
    print(json.dumps({'manifest_sha256':manifest_sha,'report_sha256':report_sha,'result_counts':report['result_counts'],'unique_urls':report['unique_frozen_urls']},indent=2))
    if args.command=='preview': return
    registry=json.loads(REGISTRY.read_text()); existing={x['protocol_id'] for x in registry['cards']}; seq=max(x['registry_sequence'] for x in registry['cards'])+1
    new=[]
    for row in rows:
        if row['claim_id'] in existing: raise SystemExit(f"already registered: {row['claim_id']}")
        eid=f"CLAIMBOUND-{row['claim_id']}-{date}"
        boundary=f"Issue #166 gate-specific audit of the frozen claim: {row['frozen_candidate_claim']} Outcome is limited to one preselected source and the frozen {row['evaluation_method']} rule."
        card={'access_date':date,'ai_assistance':'AI-assisted deterministic execution; frozen rules, source metadata, and non-pass preservation are recorded in the sanitized report.',
              'baseline_control_summary':'The exact gate-specific frozen rule evaluated true on the independently selected topic source.' if row['result_status']=='PASSED_UNDER_PROTOCOL' else None,
              'card_svg_rendered':f'docs/evidence_cards/{eid}.svg','card_svg_template':'docs/assets/claimbound_evidence_card.svg','claim_boundary':boundary,'claim_type':'source_boundary',
              'created_at':date,'domain':row['domain_slug'],'evidence_id':eid,'evidence_url':f'https://github.com/ClaimBound/claimbound-evidence/blob/main/docs/evidence_cards/{eid}.json',
              'execution_mode':'AUTOMATED_AI_ASSISTED','git_commit':'local-before-merge','known_limitations':['One exact public source per topic; no domain-wide certification.','Rules test disclosed source properties, not real-world product performance.','INSUFFICIENT_COVERAGE is not a negative result.'],
              'last_verified_date':date,'manual_review':'Operator requested honest claim-level execution; machine-observed checks are preserved for review.','official_source_name':row['source_name'],
              'official_source_url':row['source_url'],'operator':args.operator,'protocol_id':row['claim_id'],'protocol_version':PROTOCOL,'raw_payload_committed':False,
              'raw_payload_manifest':f"HTTP {row['http_status']}; canonical {row['canonical_url']}; SHA-256 {row['sha256']}; manifest {manifest_sha}; raw bytes retained locally only",
              'record_type':'source_audit','registry_sequence':seq,'reproduction_level':'not independently reproduced','result_status':row['result_status'],
              'runner_command':'uv run python scripts/claimbound_run_claim_batch_166_v2.py publish --operator <handle>','sanitized_report_path':str(REPORT.relative_to(ROOT)),
              'sanitized_report_sha256':report_sha,'source_rights_note':'Official public source; raw response bytes are not committed.','verification_count':1,
              'verification_level':'SINGLE_OPERATOR','source_manifest_sha256':manifest_sha}
        if card['baseline_control_summary'] is None: card.pop('baseline_control_summary')
        if row['result_status']=='BLOCKED_SOURCE': card['block_reason']=row['error'] or f"HTTP {row['http_status']} from the frozen URL; no substitute used"
        violations=validate_evidence_card(card)
        if violations: raise SystemExit(f"{row['claim_id']}: {'; '.join(violations)}")
        path=CARDS/f'{eid}.json'; path.write_text(json.dumps(card,indent=2,ensure_ascii=False)+'\n'); (CARDS/f'{eid}.svg').write_text(render_svg(path)); new.append(registry_entry(card,path)); seq+=1
    registry['cards'].extend(new); registry['cards'].sort(key=lambda x:x['evidence_id']); registry['card_count']=len(registry['cards'])
    registry['statistics']={'by_domain':dict(sorted(Counter(x['domain'] for x in registry['cards']).items())),'by_record_type':dict(sorted(Counter(x['record_type'] for x in registry['cards']).items())),'by_result_status':dict(sorted(Counter(x['result_status'] for x in registry['cards']).items())),'by_source':dict(sorted(Counter(x['official_source_name'] for x in registry['cards']).items()))}
    REGISTRY.write_text(json.dumps(registry,indent=2,ensure_ascii=False)+'\n'); print(f'registered_cards={len(new)} registry_card_count={registry["card_count"]}')

if __name__=='__main__': main()
