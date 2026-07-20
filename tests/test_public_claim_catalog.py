from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pytest
SCRIPT=Path(__file__).resolve().parents[1]/'scripts/build_public_claim_catalog.py'
def mod():
    spec=importlib.util.spec_from_file_location('public_claim_catalog',SCRIPT); assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def test_exact_counts_and_site(tmp_path):
    m=mod(); ds=m.domains(); claims=m.make_claims(ds); m.validate(ds,claims)
    assert len(ds)==100 and len(claims)==7000 and len({x['claim_id'] for x in claims})==7000
    assert all(x['status']=='PENDING_SOURCE_SELECTION' and x['source_url'] is None for x in claims)
    out=tmp_path/'site'; m.build(out,ds,claims)
    assert len(list((out/'domains').glob('*/index.html')))==100
    batches=list((out/'issues').glob('batch-*.md')); assert len(batches)==34
    assert max(x.stat().st_size for x in batches)<65_536
    assert sum(1 for _ in (out/'catalog.jsonl').open(encoding='utf-8'))==7000
def test_candidate_boundary_visible(tmp_path):
    m=mod(); ds=m.domains(); out=tmp_path/'site'; m.build(out,ds,m.make_claims(ds))
    page=(out/'domains/pharmaceuticals/index.html').read_text(encoding='utf-8')
    assert 'not evidence' in page.lower()
    assert 'PENDING_SOURCE_SELECTION' in page
    assert 'Open one verification issue' in page

def _manifest(m, claims, url_count):
    entries=[]
    for claim in claims:
        entries.append({
            'claim_id':claim['claim_id'],
            'source_url':f"https://sources.claimbound.org/source-{((claim['topic_index']-1)%url_count)+1}",
            'evaluation_method':m.GATE_METHODS[claim['gate']],
            'frozen_parameters':{'version':'v1'},
            'support_rule':'all preregistered gate conditions are met',
            'negative_rule':'use negative only for an explicit protocol-defined contradiction',
        })
    return {'batch_issue':166,'entries':entries}

def test_execution_manifest_rejects_one_generic_source_per_domain(tmp_path):
    m=mod(); claims=[c for c in m.make_claims(m.domains()) if c['domain_code']=='DOM001']
    path=tmp_path/'manifest.json'; path.write_text(json.dumps(_manifest(m,claims,1)))
    with pytest.raises(SystemExit,match='7 URLs minimum'):
        m.validate_execution_manifest(path)

def test_execution_manifest_accepts_gate_specific_topic_sources(tmp_path,capsys):
    m=mod(); claims=[c for c in m.make_claims(m.domains()) if c['domain_code']=='DOM001']
    path=tmp_path/'manifest.json'; path.write_text(json.dumps(_manifest(m,claims,7)))
    m.validate_execution_manifest(path)
    assert 'execution_manifest_entries=70' in capsys.readouterr().out

def test_execution_manifest_rejects_placeholder_sources(tmp_path):
    m=mod(); claims=[c for c in m.make_claims(m.domains()) if c['domain_code']=='DOM001']
    payload=_manifest(m,claims,7)
    for entry in payload['entries']: entry['source_url']=entry['source_url'].replace('sources.claimbound.org','example.org')
    path=tmp_path/'manifest.json'; path.write_text(json.dumps(payload))
    with pytest.raises(SystemExit,match='placeholder source_url forbidden'):
        m.validate_execution_manifest(path)

def test_execution_manifest_rejects_topic_url_drift(tmp_path):
    m=mod(); claims=[c for c in m.make_claims(m.domains()) if c['domain_code']=='DOM001']
    payload=_manifest(m,claims,7); payload['entries'][1]['source_url']='https://official.test/drift'
    path=tmp_path/'manifest.json'; path.write_text(json.dumps(payload))
    with pytest.raises(SystemExit,match='one frozen URL'):
        m.validate_execution_manifest(path)
