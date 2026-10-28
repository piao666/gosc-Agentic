"""Independent calibration evidence checks; no local project execution."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from scripts import audit_information_calibration as audit

ROOT = Path(__file__).resolve().parents[1]


def test_independent_gzip_reader_checks_both_wire_and_uncompressed_hash(tmp_path):
    path = tmp_path / 'observations.jsonl.gz'
    raw = b'{"event":"first","all":[1,2]}\n{"event":"second"}\n'
    path.write_bytes(gzip.compress(raw, compresslevel=1))
    meta = dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                uncompressed_sha256=hashlib.sha256(raw).hexdigest(),rows=2,
                compressed_bytes=path.stat().st_size,uncompressed_bytes=len(raw))
    assert list(audit.read_artifact(tmp_path,meta)) == [json.loads(x) for x in raw.splitlines()]
    invalid = copy.deepcopy(meta); invalid['uncompressed_sha256']='0'*64
    with pytest.raises(ValueError,match='hash|SHA'):
        list(audit.read_artifact(tmp_path,invalid))
    path.write_bytes(path.read_bytes()+b'corruption')
    with pytest.raises(ValueError,match='hash|SHA'):
        list(audit.read_artifact(tmp_path,meta))


def test_independent_selector_binding_rejects_detached_and_duplicate_rows():
    selected = [{'kind':'EVID','rate':1.,'symbols':4,'bits':4,'cell':None,'n_records':1}]
    decision = dict(event='decision',t=2,sender=0,form='scale',groups_before_age=[],selected=selected)
    numeric = dict(t=2,sender=0,original_form='scale',selected={'scale':selected,'price':selected},
                   replay_matches_actual=True,scale_price_same=True)
    assert audit.audit_selector([decision],[numeric])['replay_mismatches'] == 0
    tampered=copy.deepcopy(numeric);tampered['selected']={'scale':[],'price':[]}
    with pytest.raises(ValueError):audit.audit_selector([decision],[tampered])
    with pytest.raises(ValueError):audit.audit_selector([decision],[numeric,numeric])


def test_independent_budget_projection_accounts_for_all_cases_and_costs():
    p = json.loads((ROOT/'research/protocols/information_calibration_v1.json').read_text())
    ids=p['arms']+p['simple_references']
    rows=[dict(case_id=case,end_to_end_wall_seconds=1. if seed==0 else 2.,artifact_bytes=100 if seed==0 else 200)
          for case in ids for seed in (0,1)]
    got=audit.recompute_projection(rows,p)
    assert got['projected_seconds'] == pytest.approx(2*12*400/96*13*2)
    assert got['projected_bytes'] >= 2*12*400/96*13*200


def test_independent_numeric_comparison_rejects_changed_estimate():
    audit.assert_same({'gain':1.5,'ci':[None,2.]},{'gain':1.5,'ci':[None,2.]})
    with pytest.raises(ValueError):audit.assert_same({'gain':1.5},{'gain':2.})
    with pytest.raises(ValueError):audit.assert_same({'gain':1.5},{'gain':1.5,'new':True})


def test_independent_budget_proof_binds_exact_files(tmp_path,monkeypatch):
    p=json.loads((ROOT/'research/protocols/information_calibration_v1.json').read_text())
    rows=[dict(case_id=c,end_to_end_wall_seconds=.01,artifact_bytes=100) for c in p['arms']+p['simple_references'] for _ in p['budget_seeds']]
    data=dict(phase='budget',rows=rows,frozen={'plan':p})
    monkeypatch.setattr(audit,'verify_files',lambda *args:(data,{'status':'passed','frozen_sha256':audit.digest(tmp_path/'frozen.json')}))
    frozen=tmp_path/'frozen.json';frozen.write_text('{}')
    results=tmp_path/'results.json';results.write_text('{}')
    budget=tmp_path/'budget.json'
    budget.write_text(json.dumps(dict(**audit.recompute_projection(rows,p),gate_passed=True,
        free_bytes=p['minimum_free_bytes'],results_sha256=audit.digest(results),frozen_sha256=audit.digest(frozen))))
    proof=audit.audit_budget(results,budget,frozen)
    assert proof['status']=='passed' and proof['budget_sha256']==audit.digest(budget)
    tampered=json.loads(budget.read_text());tampered['results_sha256']='0'*64;budget.write_text(json.dumps(tampered))
    with pytest.raises(ValueError,match='binding'):
        audit.audit_budget(results,budget,frozen)
