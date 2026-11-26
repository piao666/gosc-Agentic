"""New D01-D12 contracts: only invented strings, simulated I/O, no model/network."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import time
import subprocess
import sys

import pytest

from extensions.masbench_reasoning import fair_final_v2_live as live
from extensions.masbench_reasoning import fair_final_v2 as frozen
from extensions.masbench_reasoning import fair_final_v2_runtime as newapp
from extensions.masbench_reasoning.application import PrivateView
from extensions.masbench_reasoning.execution_safety import SafetyError, canonical, digest
from extensions.masbench_reasoning.fair_final_v2_guard import FairLedger, FixtureDriver

INPUTS='research/logs/masbench-t3rv2-deployment-2026-11-26/probe_inputs.json'


def approval():
    return dict(schema='t3rv2-synthetic-live-approval-v1',approved=True,scope=live.SCOPE,
                run_id='fixture',generation_cap=2,task_generation_cap=0,monitoring_approved=True,
                context=16384,http_caps=live.CAPS,wall_seconds=2000,max_output=512,helper_attempts=2,
                protocol_sha256='1'*64)


@pytest.mark.parametrize('change',[{'approved':False},{'scope':'T3 frozen four development families'},
    {'schema':'old-T3'},{'task_generation_cap':48},{'monitoring_approved':False},{'run_id':'other'}])
def test_D01_new_approval_rejects_old_and_drift(change):
    a=approval();a.update(change)
    with pytest.raises(SafetyError):live.validate_approval(a,'fixture')


def test_D02_parent_journal_reopen_no_refund(tmp_path):
    with live.LiveBudget(tmp_path/'ledger',{'fixed':'identity'},['a','b'],wall=120) as l:
        l.episode('a','started');l.reserve_request('a/t0','a',700,512)
        l.charge('generation','/v1/chat/completions',dict(model=live.MODEL,messages=[],temperature=0,max_tokens=512,stream=False))
        l.finish_request('a/t0','failed',None,True)
        started=l.state['started_mono']
    with live.LiveBudget(tmp_path/'ledger',{'fixed':'identity'},['a','b'],wall=120) as l:
        assert l.state['started_mono']==started
        assert l.state['inputs']==700 and l.state['outputs']==512
        assert l.state['http']['generation']==1
        with pytest.raises(SafetyError):l.episode('b','started')


@pytest.mark.parametrize('category,path,body',[
    ('get','/api/chat',None),('render','/api/chat',{'model':live.MODEL}),
    ('unload','/api/chat',dict(model='other',messages=[],keep_alive=0,stream=False)),
    ('generation','/v1/chat/completions',dict(model=live.MODEL,messages=[],temperature=0,max_tokens=513,stream=False)),
    ('lifecycle_get','https://elsewhere',None)])
def test_D03_HTTP_whitelist(category,path,body):
    with pytest.raises(SafetyError):live.validate_http(category,path,body)


def test_D03_failed_attempt_is_not_refunded(tmp_path):
    with live.LiveBudget(tmp_path/'ledger',{},['a']) as l:
        l.charge('lifecycle_get','/api/version')
        # Simulated connection error occurs after the durable reservation.
        assert l.state['http']['lifecycle_get']==1
        l.fence('simulated-connect-error')
        assert l.state['http']['lifecycle_get']==1


def counted(messages,p=700):
    text='Artificial rendered text '+digest(messages)
    ids=list(range(p))
    return dict(vocab_only=True,tensor_context_created=False,template_sha256=live.primitives.TEMPLATE,
        add_special=False,parse_special=True,requests=[dict(token_count=p,token_ids=ids,
            token_ids_json_sha256=hashlib.sha256(canonical(ids)).hexdigest(),rendered=text,
            rendered_sha256=hashlib.sha256(text.encode()).hexdigest(),utf8_bytes=len(text.encode()))])


@pytest.mark.parametrize('fault',['render','ids','overflow','tensor'])
def test_D04_complete_counter_proof(fault):
    messages=[dict(role='system',content='artificial')];v=counted(messages)
    if fault=='render':v['requests'][0]['rendered']='changed'
    if fault=='ids':v['requests'][0]['token_ids'].append(0)
    if fault=='overflow':v=counted(messages,15873)
    if fault=='tensor':v['tensor_context_created']=True
    with pytest.raises(SafetyError):live.verify_count(messages,v)


@pytest.mark.parametrize('index',[0,1])
def test_D05_literal_assets_equal_actual_Agent_requests(index):
    case=json.loads((live.ROOT/INPUTS).read_bytes())['cases'][index]
    local=json.loads(case['messages'][1]['content'])
    agent=frozen.Agent(PrivateView('Alice','Bob',local['question'],local['information']))
    assert agent.request(0)==case['messages']
    assert hashlib.sha256(frozen.canonical(case['messages']).encode()).hexdigest()==case['messages_sha256']


@pytest.mark.parametrize('condition',['Full','No-A2A'])
def test_D06_independent_six_slots_match_frozen_entry(tmp_path,condition):
    outputs=['Alice: MESSAGE\n<R>Alpha is red.</R>','Bob: MESSAGE\n<R>Beta is blue.</R>',
             'Alice: MESSAGE\n<R>Alpha is red.</R>','Bob: MESSAGE\n<R>Beta is blue.</R>',
             'Alice: FINAL\n<E>LOCAL</E>\n<A>PRIVATE_ALPHA_FINAL</A>',
             'Bob: FINAL\n<E>LOCAL</E>\n<A>PRIVATE_BETA_FINAL</A>']
    views=[PrivateView('Alice','Bob','Artificial question','PRIVATE_ALPHA'),
           PrivateView('Bob','Alice','Artificial question','PRIVATE_BETA')]
    results=[]
    for i,entry in enumerate((frozen.run_episode,newapp.run_episode)):
        plan=[dict(id='e',family='artificial',condition=condition,partition='task')]
        with FairLedger(tmp_path/str(i),plan) as l:
            d=FixtureDriver(l,outputs)
            r=entry(views,d,condition,'e');assert r['completed'];results.append(r)
    for key in ('memory','received_sources','finals','accounting'):
        assert results[0][key]==results[1][key]
    # Measured host CPU duration is an observation, not a deterministic wire
    # state. Both raw values remain in the fixture journals/results.
    for r in results:
        assert type(r['wire_totals']['cpu_process_ns']) is int and r['wire_totals']['cpu_process_ns']>=0
    assert {k:v for k,v in results[0]['wire_totals'].items() if k!='cpu_process_ns'}== \
           {k:v for k,v in results[1]['wire_totals'].items() if k!='cpu_process_ns'}
    assert [s['request'] for s in results[0]['slots']]==[s['request'] for s in results[1]['slots']]
    bob=frozen.canonical(results[1]['slots'][5]['request'])
    assert 'PRIVATE_ALPHA_FINAL' not in bob


@pytest.fixture
def simulated_driver(tmp_path,monkeypatch):
    monkeypatch.setattr(live,'HDD',tmp_path/'hdd')
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'input_assets':INPUTS}))
    monkeypatch.setattr(live,'PLAN',plan)
    a=approval();root=live.HDD/a['run_id'];budget=live.LiveBudget(root/'budget',{},['deploy-short','deploy-long'])
    runtime=live.primitives.Runtime(str(live.ROOT),live.HELPER,1,'stamp',live.BINARY_SHA,16384)
    owner=b'fixture-owner';lease=SimpleNamespace(owner=lambda:owner)
    monitor=lambda **unused:dict(driver_rss=1,service_rss=1,gpu_bytes=0)
    monkeypatch.setattr(live.primitives,'runtime_files',lambda r:tmp_path/'models')
    state={'loaded':False,'usage_missing':False,'foreign':False,'render':None,'tokens':None}
    monkeypatch.setattr(live.primitives,'runner_identities',lambda r:([dict(pid=20 if state['foreign'] else 10,stamp='s')]
                                                                     if state['loaded'] else []))
    monkeypatch.setattr(live.primitives,'proc_stamp',lambda pid:'s' if state['loaded'] else None)
    d=live.LiveDriver(root,runtime,budget,a,lease,owner,monitor)
    class FakeRPC:
        def call(self,spec,timeout):
            if spec['kind']=='counter':
                messages=spec['input']['requests'][0]['messages']
                v=counted(messages,2000 if len(frozen.canonical(messages))>10000 else 700)
                v['input_sha256']=hashlib.sha256(canonical(spec['input'])).hexdigest()
                state['render']=v['requests'][0]['rendered'];state['tokens']=v['requests'][0]['token_count'];return v
            category,path,body=spec['category'],spec['path'],spec['body']
            if category=='render':state['loaded']=True;return {'_debug_info':{'rendered_template':state['render']}}
            if category=='unload':state['loaded']=False;return dict(done=True,done_reason='unload')
            if path=='/api/version':return {'version':'0.11.11'}
            if path=='/api/ps':return dict(models=[dict(name=live.MODEL,digest=live.primitives.MANIFEST,context_length=16384)] if state['loaded'] else [])
            if category=='generation':
                p=state['tokens']
                return dict(model=live.MODEL,choices=[dict(finish_reason='stop',message=dict(content='Alice: MESSAGE\n<R>The artificial parcel is blue.</R>'))],
                            usage=None if state['usage_missing'] else dict(prompt_tokens=p,completion_tokens=17,total_tokens=p+17))
            raise AssertionError('unexpected simulated operation')
    d.rpc=FakeRPC()
    yield d,state
    budget.close()


def short_messages():return json.loads((live.ROOT/INPUTS).read_bytes())['cases'][0]['messages']


def test_D07_unknown_usage_fences_and_retains_budget(simulated_driver):
    d,s=simulated_driver;s['usage_missing']=True;d.begin('deploy-short')
    with pytest.raises(Exception):d.generate(short_messages(),'deploy-short',0)
    d.abort('deploy-short','unknown_usage')
    assert d.ledger.state['outputs']==512 and d.ledger.state['inputs']==700
    assert d.ledger.state['requests']['deploy-short/t0']['observed_usage'] is None
    with pytest.raises(SafetyError):d.begin('deploy-long')


def test_D08_packet_excess_and_unfrozen_request(simulated_driver):
    d,s=simulated_driver;d.begin('deploy-short')
    bad=[dict(role='system',content='x'*65537)]
    with pytest.raises(SafetyError):live.verify_count(bad,counted(bad))
    with pytest.raises(SafetyError):d.generate(bad,'deploy-short',0)
    assert sum(d.ledger.state['http'].values())==0


def test_D09_single_cleanup_runner_exit(simulated_driver):
    d,s=simulated_driver;d.begin('deploy-short');raw,row=d.generate(short_messages(),'deploy-short',0)
    d.end('deploy-short')
    assert d.ledger.state['cleanup']['deploy-short']=='verified'
    assert d.ledger.state['http']['unload']==1 and not s['loaded']
    with pytest.raises(SafetyError):d.cleanup('deploy-short')


def test_D09_foreign_runner_never_unloaded(simulated_driver):
    d,s=simulated_driver;d.begin('deploy-short');d.generate(short_messages(),'deploy-short',0)
    s['foreign']=True
    with pytest.raises(SafetyError):d.cleanup('deploy-short')
    assert d.ledger.state['http']['unload']==0


def test_D01_baseline_PID_drift_before_service_change(simulated_driver,tmp_path,monkeypatch):
    from experiments_ext import masbench_t3rv2_live_probe as launcher
    d,s=simulated_driver
    deployment=launcher.Deployment(d,SimpleNamespace(bind=lambda *a,**k:None),tmp_path)
    monkeypatch.setattr(deployment,'runtime',lambda context:d.runtime)
    with pytest.raises(SafetyError,match='baseline_PID_stamp_drift'):deployment.enter()
    assert d.ledger.state['operations']['start']==d.ledger.state['operations']['stop']==0


def test_D10_tail_reserve_and_attempt_caps(simulated_driver,monkeypatch):
    d,s=simulated_driver;d.begin('deploy-short')
    monkeypatch.setattr(d.ledger,'remaining',lambda:100)
    with pytest.raises(SafetyError):d.generate(short_messages(),'deploy-short',0)
    assert d.ledger.state['operations']['counter']==0
    d.ledger.operation('start');d.ledger.operation('start')
    with pytest.raises(SafetyError):d.ledger.operation('start')


def test_D10_service_limits_do_not_inherit_narrowed_driver(tmp_path):
    # This is a fixed Python fixture subprocess, never Ollama. Its pre-existing
    # spawner retains 256MiB while the driver child narrows itself to 64MiB.
    code='''
import json,resource
from experiments_ext.masbench_t3rv2_live_probe import ServiceSpawner
p=ServiceSpawner(fixture=True)
resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2))
r=p.request({'fixture':'report-inherited-limit'})
p.close()
print(json.dumps(dict(driver=list(resource.getrlimit(resource.RLIMIT_AS)),service=r['service_AS'])))
'''
    p=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=10)
    assert p.returncode==0,p.stderr
    v=json.loads(p.stdout)
    assert v['driver']==[64*1024**2]*2 and v['service']==[256*1024**2]*2


@pytest.mark.parametrize('fault',['RSS','gap','gpu'])
def test_D11_resource_observation_and_sampling_fail_closed(tmp_path,monkeypatch,fault):
    from experiments_ext import masbench_t3rv2_live_probe as launcher
    with live.LiveBudget(tmp_path/'ledger',{},['a']) as budget:
        monitor=launcher.Monitor(budget)
        monkeypatch.setattr(launcher,'process_rss',lambda *unused:(3*1024**3 if fault=='RSS' else 1,1))
        monkeypatch.setattr(launcher.subprocess,'check_output',lambda *a,**k:'17000' if fault=='gpu' else '0')
        if fault=='gap':monitor.last=time.monotonic()-1
        with pytest.raises(SafetyError):monitor(force=True)


def test_D12_complete_transfer_includes_failures():
    expected={'failed-prefix':hashlib.sha256(b'failure').hexdigest()}
    assert live.verify_complete_download(expected,{'failed-prefix':b'failure'})
    with pytest.raises(SafetyError):live.verify_complete_download(expected,{})
    with pytest.raises(SafetyError):live.verify_complete_download(expected,{'failed-prefix':b'changed'})
