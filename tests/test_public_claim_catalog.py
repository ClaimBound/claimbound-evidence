from __future__ import annotations
import importlib.util
from pathlib import Path
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
