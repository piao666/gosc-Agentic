"""HPC-only contracts for an explicit, bounded resource amendment."""
import copy
import json
from pathlib import Path

import pytest

from scripts import repro_information_calibration_amendment as wrapper


def inputs(tmp_path):
    frozen = tmp_path / 'frozen.json'; frozen.write_text('{}')
    budget = tmp_path / 'budget.json'; budget.write_text('{}')
    audit = tmp_path / 'audit.json'; audit.write_text('{}')
    amendment = dict(status='approved', user_authorized=True,
        parent_frozen_sha256=wrapper.base.digest(frozen), budget_sha256=wrapper.base.digest(budget),
        budget_audit_sha256=wrapper.base.digest(audit), resource_overrides=dict(wrapper.RESOURCE_OVERRIDES),
        formal_test_authorized=False, training=False)
    return frozen, budget, audit, amendment


def test_amendment_requires_explicit_approval_and_exact_resource_limits(tmp_path):
    frozen, budget, audit, amendment = inputs(tmp_path)
    assert wrapper.validate_amendment(amendment, frozen, budget, audit) == wrapper.RESOURCE_OVERRIDES
    for key, value in [('status','pending'), ('user_authorized',False),
                       ('formal_test_authorized',True), ('training',True)]:
        invalid=copy.deepcopy(amendment);invalid[key]=value
        with pytest.raises(RuntimeError):
            wrapper.validate_amendment(invalid,frozen,budget,audit)
    invalid=copy.deepcopy(amendment);invalid['resource_overrides']['calibration_timeout_seconds']=2401
    with pytest.raises(RuntimeError):wrapper.validate_amendment(invalid,frozen,budget,audit)


def test_amendment_rejects_scientific_override_and_unbound_inputs(tmp_path):
    frozen,budget,audit,amendment=inputs(tmp_path)
    for where in ('resource_overrides','top'):
        invalid=copy.deepcopy(amendment)
        (invalid if where=='top' else invalid['resource_overrides'])['calibration_seeds']=[1]
        with pytest.raises(RuntimeError):wrapper.validate_amendment(invalid,frozen,budget,audit)
    for field in ('parent_frozen_sha256','budget_sha256','budget_audit_sha256'):
        invalid=copy.deepcopy(amendment);invalid[field]='0'*64
        with pytest.raises(RuntimeError):wrapper.validate_amendment(invalid,frozen,budget,audit)


def test_effective_frozen_changes_only_resources_and_adds_source_provenance(tmp_path,monkeypatch):
    monkeypatch.setattr(wrapper,'ROOT',tmp_path)
    frozen,budget,audit,amendment=inputs(tmp_path)
    original=tmp_path/'original.py';original.write_text('original\n')
    code=tmp_path/'wrapper.py';code.write_text('wrapper\n')
    test=tmp_path/'test.py';test.write_text('test\n')
    approval=tmp_path/'approval.json';approval.write_text(json.dumps(amendment))
    monkeypatch.setattr(wrapper,'source_files',lambda:[code,test])
    parent=dict(plan={'calibration_timeout_seconds':1200,'calibration_projection_gate_seconds':1080,
        'compressed_output_cap_bytes':268435456,'minimum_free_bytes':671088640,
        'calibration_seeds':[28000000],'primary_method':'paid-pose','bootstrap_resamples':20000},
        cases=[{'id':'paid-pose'}],worlds={'28000000':'a'*64},
        source_sha256={'original.py':wrapper.base.digest(original)},scientific_marker=['preserve'])
    previous=copy.deepcopy(parent)
    effective=wrapper.effective_frozen(parent,amendment,approval,frozen,budget,audit,{'contracts_run':'targeted'})
    assert parent==previous
    expected=copy.deepcopy(previous['plan']);expected.update(wrapper.RESOURCE_OVERRIDES)
    assert effective['plan']==expected
    for key in ('cases','worlds','scientific_marker'):
        assert effective[key]==previous[key]
    assert effective['source_sha256']['original.py']==previous['source_sha256']['original.py']
    assert set(effective['source_sha256'])=={'original.py','wrapper.py','test.py','approval.json'}
    assert effective['parent_frozen_sha256']==wrapper.base.digest(frozen)
    assert effective['amendment']['approval_sha256']==wrapper.base.digest(approval)
    assert frozen.read_text()=='{}' and budget.read_text()=='{}' and audit.read_text()=='{}'


def test_amendment_contracts_require_passed_unskipped_junit_and_matching_snapshot(tmp_path,monkeypatch):
    monkeypatch.setattr(wrapper,'ROOT',tmp_path)
    code=tmp_path/'wrapper.py';code.write_text('wrapper\n')
    test=tmp_path/'test.py';test.write_text('test\n')
    monkeypatch.setattr(wrapper,'source_files',lambda:[code,test])
    contracts=tmp_path/'research/sync/runs/targeted';(contracts/'outputs').mkdir(parents=True)
    (contracts/'status.json').write_text(json.dumps({'status':'completed','exit_code':0}))
    (contracts/'manifest.json').write_text(json.dumps({'kind':'test'}))
    (contracts/'source_snapshot.json').write_text(json.dumps({'files':[
        {'path':p.name,'remote_sha256':wrapper.base.digest(p)} for p in (code,test)]}))
    xml='<testsuite>'+''.join('<testcase name="'+n+'"/>' for n in wrapper.REQUIRED_CONTRACTS)+'</testsuite>'
    (contracts/'outputs/pytest.xml').write_text(xml)
    assert wrapper.validate_contracts(contracts)['contracts_run']=='targeted'
    (contracts/'outputs/pytest.xml').write_text(xml.replace('/>','><skipped/></testcase>',1))
    with pytest.raises(RuntimeError):wrapper.validate_contracts(contracts)
    (contracts/'outputs/pytest.xml').write_text(xml);code.write_text('changed\n')
    with pytest.raises(RuntimeError):wrapper.validate_contracts(contracts)


def budget_fixture(tmp_path,monkeypatch):
    frozen,budget,audit,amendment=inputs(tmp_path)
    seeds=[28100000,28100001];cases=[{'id':'case'+str(i)} for i in range(13)]
    parent=dict(plan={'budget_seeds':seeds},cases=cases,source_sha256={'old.py':'1'*64},config_sha256='2'*64)
    rows=[dict(seed=s,case_id=c['id'],phase='budget',status='completed') for s in seeds for c in cases]
    data=dict(phase='budget',frozen=parent,frozen_sha256=wrapper.base.digest(frozen),rows=rows,
              calibration_run=False,formal_test_run=False,training=False)
    results=tmp_path/'results.json';results.write_text(json.dumps(data))
    report=dict(results_sha256=wrapper.base.digest(results),frozen_sha256=wrapper.base.digest(frozen),
                source_sha256=parent['source_sha256'],config_sha256=parent['config_sha256'],
                projected_seconds=1940.,projected_bytes=279000000)
    budget.write_text(json.dumps(report))
    proof=dict(status='blocked',phase='budget',rows=26,budget_sha256=wrapper.base.digest(budget),
        results_sha256=wrapper.base.digest(results),frozen_sha256=wrapper.base.digest(frozen),
        projected_seconds=1940.,projected_bytes=279000000,
        input_sha256={'results.json':wrapper.base.digest(results)},
        details=[{'seed':r['seed'],'case_id':r['case_id']} for r in rows])
    audit.write_text(json.dumps(proof))
    monkeypatch.setattr(wrapper.base,'project_budget',lambda *a:{'projected_seconds':1940.,'projected_bytes':279000000})
    return parent,frozen,budget,audit,proof,report


def test_amendment_accepts_audited_blocked_budget_only_with_exact_complete_matrix(tmp_path,monkeypatch):
    parent,frozen,budget,audit,proof,report=budget_fixture(tmp_path,monkeypatch)
    assert wrapper.validate_budget_proof(parent,frozen,budget,audit)['projected_seconds']==1940.
    for field,value in [('rows',25),('status','failed'),('budget_sha256','0'*64),('frozen_sha256','0'*64)]:
        altered=copy.deepcopy(proof);altered[field]=value;audit.write_text(json.dumps(altered))
        with pytest.raises(RuntimeError):wrapper.validate_budget_proof(parent,frozen,budget,audit)
    audit.write_text(json.dumps(proof))
    results=tmp_path/'results.json';data=json.loads(results.read_text());data['rows'][-1]=data['rows'][0]
    results.write_text(json.dumps(data))
    with pytest.raises(RuntimeError):wrapper.validate_budget_proof(parent,frozen,budget,audit)


def test_amendment_resource_gate_blocks_excess_projection_and_low_disk():
    wrapper.validate_resource_gate({'projected_seconds':1940.,'projected_bytes':279000000},939524096)
    for values,free in [({'projected_seconds':2160.1,'projected_bytes':100},939524096),
                         ({'projected_seconds':1.,'projected_bytes':402653185},939524096),
                         ({'projected_seconds':1.,'projected_bytes':100},939524095)]:
        with pytest.raises(RuntimeError):wrapper.validate_resource_gate(values,free)


def test_amendment_run_records_effective_freeze_before_unchanged_calibration_loop(tmp_path,monkeypatch):
    frozen,budget,audit,amendment=inputs(tmp_path)
    (tmp_path/'results.json').write_text('{}')
    approval=tmp_path/'approval.json';approval.write_text(json.dumps(amendment))
    parent={'plan':{},'source_sha256':{}}
    monkeypatch.setattr(wrapper.base,'read',lambda p: amendment if Path(p)==approval else parent)
    monkeypatch.setattr(wrapper.base,'validate_frozen',lambda f:None)
    monkeypatch.setattr(wrapper,'validate_parent_contracts',lambda f:None)
    monkeypatch.setattr(wrapper,'validate_contracts',lambda p:{'contracts_run':'ok'})
    monkeypatch.setattr(wrapper,'validate_budget_proof',lambda *a:{'projected_seconds':1940.,'projected_bytes':279000000})
    monkeypatch.setattr(wrapper,'validate_resource_gate',lambda *a:None)
    monkeypatch.setattr(wrapper,'effective_frozen',lambda *a:{'plan':dict(wrapper.RESOURCE_OVERRIDES),'source_sha256':{}})
    monkeypatch.setattr(wrapper.base,'check_sources',lambda f:None)
    output=tmp_path/'outputs';output.mkdir()
    calls=[]
    def execute(derived,out,phase,path):
        assert phase=='calibration' and out==output
        assert path.name=='effective_frozen.json' and path.exists()
        assert (output/'budget-authorization.json').exists()
        calls.append((derived,phase));return {'status':'fixture'}
    monkeypatch.setattr(wrapper.base,'run_matrix',execute)
    monkeypatch.setattr(wrapper.base,'calibrate',lambda *a:pytest.fail('Original gate must remain intact'))
    result=wrapper.run(frozen,budget,audit,approval,tmp_path/'contracts',output)
    assert result=={'status':'fixture'} and len(calls)==1
    assert frozen.read_text()=='{}' and budget.read_text()=='{}'


def test_amendment_cli_exposes_only_explicit_run_with_all_proofs():
    parser=wrapper.build_parser()
    args=parser.parse_args(['--mode','run','--frozen','f','--budget','b','--budget-audit','a',
                            '--amendment','p','--contracts-run','c'])
    assert args.mode=='run'
    with pytest.raises(SystemExit):parser.parse_args(['--mode','calibrate'])


def test_amendment_parent_full_contract_proof_requires_379_and_unchanged_hashes(tmp_path,monkeypatch):
    monkeypatch.setattr(wrapper,'ROOT',tmp_path)
    contracts=tmp_path/'research/sync/runs/full';(contracts/'outputs').mkdir(parents=True)
    (contracts/'status.json').write_text('{"status":"completed","exit_code":0}')
    (contracts/'outputs/pytest.xml').write_text('<testsuite/>')
    parent=dict(contracts_run='full',contract_tests=379,source_sha256={'original.py':'a'*64},
        config_path='config.json',contracts_status_sha256=wrapper.base.digest(contracts/'status.json'),
        junit_sha256=wrapper.base.digest(contracts/'outputs/pytest.xml'))
    count=[379]
    monkeypatch.setattr(wrapper.base,'validate_contracts',lambda *a:(parent['source_sha256'],count[0]))
    assert wrapper.validate_parent_contracts(parent)['contract_tests']==379
    count[0]=378
    with pytest.raises(RuntimeError):wrapper.validate_parent_contracts(parent)
    count[0]=379;(contracts/'status.json').write_text('{"changed":true}')
    with pytest.raises(RuntimeError):wrapper.validate_parent_contracts(parent)
