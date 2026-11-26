"""New T01-T16 task wiring contracts. Artificial views; never native tasks/gold."""
import copy,hashlib,json,os,subprocess,sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import pytest
from extensions.masbench_reasoning import fair_final_v2_task as t
from extensions.masbench_reasoning.fair_final_v2 import Agent,parse_output
from extensions.masbench_reasoning.fair_final_v2_task_campaign import run_campaign,preflight_initial_inputs
from extensions.masbench_reasoning.fair_final_v2_guard import FixtureCounter,PacketBudget,resource_guard
from extensions.masbench_reasoning.fair_final_v2_scoring import score_episode,paired_summary
from extensions.masbench_reasoning.fixture_driver import _jsonable
from extensions.masbench_reasoning.execution_safety import SafetyError,canonical,digest
from extensions.masbench_reasoning.application import PrivateView


def setup():
    plan=[];views={}
    for i in range(4):
        f='invented-family-'+str(i)
        views[f]=[PrivateView('Alice','Bob','Artificial parcel '+str(i),'LOCAL_ALICE_'+str(i)),PrivateView('Bob','Alice','Artificial parcel '+str(i),'LOCAL_BOB_'+str(i))]
        for c in (['Full','No-A2A'] if i%2==0 else ['No-A2A','Full']):
            plan.append(dict(id=f+'-'+c,family=f,condition=c,partition='task',private_view_sha256=digest([asdict(v) for v in views[f]])))
    return plan,views


def outputs():return ['Alice: MESSAGE\n<R>Invented alpha is red.</R>','Bob: MESSAGE\n<R>Invented beta is blue.</R>','Alice: MESSAGE\n<R>Invented alpha is red.</R>','Bob: MESSAGE\n<R>Invented beta is blue.</R>','Alice: FINAL\n<E>LOCAL</E>\n<A>SECRET_ALICE_FINAL</A>','Bob: FINAL\n<E>LOCAL</E>\n<A>SECRET_BOB_FINAL</A>']


def authority(plan):return dict(schema='t3rv2t-task-approval-v1',approved=True,scope=t.SCOPE,run_id='fixture',generation_cap=48,synthetic_cap=0,http_caps=t.CAPS,wall_seconds=18360,monitoring_approved=True,plan_sha256=digest(plan),previous_probe_generations=2,old_2000s_deadline_reopened=False,protocol_sha256='1'*64,baseline_pid=1,baseline_stamp='fixture-only')


def test_T01_full_plan_reset_isolation_and_fixture_label(tmp_path):
    plan,views=setup();saved={}
    with t.TaskLedger(tmp_path/'budget',plan,fixture=True) as l:
        ds=[]
        def factory(row):
            d=t.TaskFixtureDriver(l,outputs());ds.append(d);return d
        results=run_campaign(plan,views,factory,lambda k,r:saved.update({k:r}))
        assert t.engineering_complete(plan,results,l,require_real=False)['passed']
        assert not t.engineering_complete(plan,results,l,require_real=True)['passed']
        assert len(l.state['requests'])==48 and l.state['outputs']==24576
        assert l.state['http']['get']==152 and l.state['http']['generation']==48
        for r,d in zip(results,ds):
            assert len(r['slots'])==6 and r['accounting']['scope'].startswith('task_fixture:')
            assert len(r['slots'][0]['request'])==3
            assert 'SECRET_ALICE_FINAL' not in canonical(r['slots'][5]['request']).decode()
            assert 'SECRET_BOB_FINAL' not in canonical(r['slots'][4]['request']).decode()
            assert all('FINAL' not in str(m.get('source',{})) for m in r['messages'])
            if r['condition']=='No-A2A':assert r['received_sources']==[{},{}] and len(r['finals'])==2
            else:assert len(r['received_sources'][0])==len(r['received_sources'][1])==2
        assert len({id(d.transport) for d in ds})==len({id(d.packets) for d in ds})==8
        state=copy.deepcopy(l.state)
        fixture=dict(plan=plan,results=_jsonable(results),state=state,budget_root=str(tmp_path/'budget'))
        Path(os.environ['GOSC_OUTPUT_DIR'],'task_fixture.json').write_bytes(canonical(fixture))


@pytest.mark.parametrize('raw',[None,'','Alice: MESSAGE\n<A>early</A>','Alice: MESSAGE\n<R>x</R>\n<A>x</A>'])
def test_T02_early_empty_illegal_exchange_never_shortens(tmp_path,raw):
    p,v=setup();o=outputs();o[0]=raw
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        d=t.TaskFixtureDriver(l,o)
        from extensions.masbench_reasoning.fair_final_v2_runtime import run_episode
        r=run_episode(v[p[0]['family']],d,'Full',p[0]['id'])
        assert r['completed'] and len(l.state['requests'])==6 and len(r['finals'])==2
        assert not r['slots'][0]['parsed']['valid_format']


@pytest.mark.parametrize('answer,valid,reason',[
 ('Alice: FINAL\n<E>LOCAL; PEER:t0</E>\n<A>x</A>',False,'invalid_final'),
 ('Alice: FINAL\n<E>LOCAL</E>\n<U>INSUFFICIENT_EVIDENCE</U>',True,'abstain'),
 ('Alice: FINAL\n<E>LOCAL</E>\n<A>answer</A>',False,'invalid_final')])
def test_T03_final_source_abstain_no_repair(tmp_path,answer,valid,reason):
    p,v=setup();o=outputs();o[4]=answer
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        from extensions.masbench_reasoning.fair_final_v2_runtime import run_episode
        r=run_episode(v[p[0]['family']],t.TaskFixtureDriver(l,o),'Full',p[0]['id'])
        assert r['completed'] and r['finals']['Alice']['valid_format']==valid and r['finals']['Alice']['reason']==reason
        s=score_episode(r,'invented-reference');assert s['scores']['Alice']['F1']==0


def test_T04_strict_bundle_rejects_gold_and_unbound_views(tmp_path):
    p,v=setup();obj=dict(schema='four-local-views-v1',families=[dict(family=f,views=[asdict(x) for x in pair]) for f,pair in v.items()])
    path=tmp_path/'views.json'
    def load(value):
        path.write_bytes(canonical(value));return t.load_private_bundle(path,hashlib.sha256(path.read_bytes()).hexdigest(),p)
    assert load(obj)==v
    for bad in [dict(obj,gold='forbidden'),dict(obj,records=[]),dict(obj,families=obj['families'][:3])]:
        with pytest.raises(SafetyError):load(bad)
    bad=copy.deepcopy(obj);bad['families'][0]['views'][0]['gold']='forbidden'
    with pytest.raises(SafetyError):load(bad)
    bad=copy.deepcopy(obj);bad['families'][0]['views'][0]['information']='changed'
    with pytest.raises(SafetyError):load(bad)


def test_T05_probe_and_unapproved_task_authority_rejected(tmp_path):
    p,_=setup();assert t.validate_task_approval(authority(p),'fixture',p)
    old=json.loads((t.ROOT/'research/protocols/masbench_t3rv2_live_authorization_2026-11-26.json').read_bytes())
    for a in [old,dict(authority(p),approved=False),dict(authority(p),synthetic_cap=2),dict(authority(p),old_2000s_deadline_reopened=True)]:
        with pytest.raises(SafetyError):t.validate_task_approval(a,'fixture',p)
    env=dict(os.environ,GOSC_RUN_DIR=str(t.ROOT/'research/sync/runs/PENDING_SINGLE_REGISTERED_RUN'))
    r=subprocess.run([sys.executable,'-m','experiments_ext.masbench_t3rv2t_task'],env=env,capture_output=True,timeout=10)
    assert r.returncode!=0 and b'task_specific_approval_required' in r.stderr


def test_T05_approved_source_must_match_contract_receipt(tmp_path,monkeypatch):
    p,_=setup();root=tmp_path/'repo';root.mkdir();a=authority(p)
    plan=root/'plan.json';plan.write_bytes(canonical(dict(episodes=p,parent_probe={'ledger_sha256':'a'*64})))
    bound={}
    for name in t.MATERIAL_FILES:
        f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'artificial source binding');bound[name]=hashlib.sha256(f.read_bytes()).hexdigest()
    receipt=root/'receipt.json';record=dict(passed=True,source_files=dict(bound));receipt.write_bytes(canonical(record))
    a.update(bound_files=bound,contract_receipt='receipt.json',contract_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),parent_probe_ledger_sha256='a'*64)
    auth=root/'authority.json';auth.write_bytes(canonical(a))
    monkeypatch.setattr(t,'ROOT',root);monkeypatch.setattr(t,'PLAN',plan);monkeypatch.setattr(t,'AUTH',auth)
    monkeypatch.setenv('GOSC_RUN_DIR',str(root/'research/sync/runs/fixture'))
    assert t.require_approval()['approved']
    record['source_files'][t.MATERIAL_FILES[0]]='0'*64;receipt.write_bytes(canonical(record));a['contract_sha256']=hashlib.sha256(receipt.read_bytes()).hexdigest();auth.write_bytes(canonical(a))
    with pytest.raises(SafetyError,match='approved_source_must_equal_tested_source'):t.require_approval()


@pytest.mark.parametrize('modes',[{0:{'usage':False}},{1:{'create_mode':'hang'}}])
def test_T06_partial_failure_denominator_no_retry_persistent(tmp_path,modes):
    p,v=setup();root=tmp_path/'b'
    with t.TaskLedger(root,p,fixture=True) as l:
        rs=run_campaign(p,v,lambda row:t.TaskFixtureDriver(l,outputs(),modes=modes,timeout=.2),lambda *a:None)
        assert len(rs)==1 and rs[0]['started'] and not rs[0]['completed']
        scored=score_episode(rs[0],'invented-reference');assert scored['mean_F1']==0 and len(scored['scores'])==2
        assert l.state['fenced'] and l.state['outputs']>=512
        assert not t.engineering_complete(p,rs,l,require_real=False)['passed']
        charged=l.state['outputs'];started=l.state['started_mono']
    with t.TaskLedger(root,p,fixture=True) as l:
        assert l.state['outputs']==charged and l.state['started_mono']==started
        with pytest.raises(SafetyError):l.episode(p[1]['id'],'started')
    assert score_episode(dict(started=False),'invented-reference')['scores'] is None


def test_T07_initial_full_input_count_and_window(tmp_path):
    p,v=setup();rows=[]
    count=lambda m:dict(request_sha256=digest(m),tokens=700)
    assert len(preflight_initial_inputs(p,v,count,rows.append))==8
    assert len(rows)==8
    with pytest.raises(SafetyError):preflight_initial_inputs(p,v,lambda m:dict(request_sha256=digest(m),tokens=15873),lambda r:None)
    with pytest.raises(SafetyError):preflight_initial_inputs(p,v,lambda m:dict(request_sha256='0'*64,tokens=1),lambda r:None)


def test_T08_limits_and_no_generated_calls_on_overwindow(tmp_path):
    p,v=setup()
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        rs=run_campaign(p,v,lambda row:t.TaskFixtureDriver(l,outputs(),counter=FixtureCounter(tokens=15873)),lambda *a:None)
        assert not rs[0]['completed'] and len(l.state['requests'])==0 and l.state['fenced']
    for values in [(2*1024**3+1,1,0),(1,16*1024**3+1,0),(1,1,16*1024**3+1)]:
        with pytest.raises(SafetyError):resource_guard(*values)
    b=PacketBudget()
    with pytest.raises(SafetyError):b.packet('x'*65536)
    b=PacketBudget(ordinary=65536,cumulative=10)
    with pytest.raises(SafetyError):b.packet('x'*20)
    with pytest.raises(SafetyError):PacketBudget(terminal=10).result({'x':'x'*20})


def test_T09_exit_barrier_and_return_failure_stop_plan(tmp_path):
    p,v=setup()
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        def factory(row):
            d=t.TaskFixtureDriver(l,outputs());d.service.stuck=True;return d
        rs=run_campaign(p,v,factory,lambda *a:None)
        assert len(rs)==1 and rs[0]['error'] and not rs[0]['completed'] and l.state['fenced']
        assert len(l.state['requests'])==6
    with t.TaskLedger(tmp_path/'return',p,fixture=True) as l:
        def fail(*args):raise OSError('synthetic return failure')
        with pytest.raises(OSError):run_campaign(p,v,lambda row:t.TaskFixtureDriver(l,outputs()),fail)
        assert len(l.state['requests'])==6 # cannot start next episode after failed return


def test_T10_storage_reservation_and_operation_caps(tmp_path):
    p,_=setup()
    with t.TaskLedger(tmp_path/'small',p,fixture=True,artifact_bytes=10000) as l:
        with pytest.raises(SafetyError):l.put_artifact('oversize',b'x'*10001)
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        for i in range(8):l.operation('precount')
        with pytest.raises(SafetyError):l.operation('precount')
        for i in range(48):l.operation('counter')
        with pytest.raises(SafetyError):l.operation('counter')
    with pytest.raises(SafetyError):t.TaskLedger(tmp_path/'b',p,fixture=False)


def counted(messages,p=700):
    text='Synthetic rendered '+digest(messages);ids=list(range(p))
    return dict(vocab_only=True,tensor_context_created=False,template_sha256=t.primitives.TEMPLATE,add_special=False,parse_special=True,requests=[dict(token_count=p,token_ids=ids,token_ids_json_sha256=digest(ids),rendered=text,rendered_sha256=hashlib.sha256(text.encode()).hexdigest(),utf8_bytes=len(text.encode()))])


@pytest.fixture
def task_driver(tmp_path,monkeypatch):
    p,v=setup();a=authority(p);monkeypatch.setattr(t,'HDD',tmp_path/'hdd');root=t.HDD/a['run_id']
    l=t.TaskLedger(root/'budget',p,fixture=False,identity=a)
    runtime=t.primitives.Runtime(str(t.ROOT),t.HELPER,1,'stamp',t.BINARY_SHA,16384)
    owner=b'fixture';lease=SimpleNamespace(owner=lambda:owner)
    monitor=lambda **unused:dict(driver_rss=1,service_rss=1,gpu_bytes=0)
    monkeypatch.setattr(t.primitives,'runtime_files',lambda r:tmp_path/'models')
    state=dict(loaded=False,epoch=0,missing=False,wrong_count=False,drift=False)
    monkeypatch.setattr(t.primitives,'runner_identities',lambda r:[dict(pid=10+state['epoch']+int(state['drift']),stamp='s')] if state['loaded'] else [])
    monkeypatch.setattr(t.primitives,'proc_stamp',lambda pid:'s' if state['loaded'] else None)
    d=t.TaskDriver(root,runtime,l,a,lease,owner,monitor)
    class FakeRPC:
        def call(self,spec,timeout):
            if spec['kind']=='counter':
                m=spec['input']['requests'][0]['messages'];reply=counted(m)
                reply['input_sha256']='0'*64 if state['wrong_count'] else digest(spec['input'])
                state['render']=reply['requests'][0]['rendered'];return reply
            cat,path=spec['category'],spec['path']
            if cat=='render':
                if not state['loaded']:state['epoch']+=1
                state['loaded']=True;return {'_debug_info':{'rendered_template':state['render']}}
            if cat=='unload':state['loaded']=False;return dict(done=True,done_reason='unload')
            if path=='/api/version':return dict(version='0.11.11')
            if path=='/api/ps':return dict(models=[dict(name=t.MODEL,digest=t.primitives.MANIFEST,context_length=16384)] if state['loaded'] else [])
            if cat=='generation':
                turn=d.next_turn-1
                return dict(model=t.MODEL,choices=[dict(finish_reason='stop',message=dict(content=outputs()[turn]))],usage=None if state['missing'] else dict(prompt_tokens=700,completion_tokens=17,total_tokens=717))
            raise AssertionError(cat)
    d.rpc=FakeRPC()
    yield d,state,p,v
    l.close()


def test_T11_task_real_adapter_all_48_are_only_simulated(task_driver):
    d,s,p,v=task_driver;rs=run_campaign(p,v,lambda row:d,lambda *a:None)
    assert t.engineering_complete(p,rs,d.ledger,require_real=True)['passed'] # interface mode only; FakeRPC disclosed!
    assert d.ledger.state['http']==dict(generation=48,render=48,get=152,cleanup_get=16,unload=8,lifecycle_get=0)
    assert d.ledger.state['operations']['counter']==48 and s['epoch']==8 and not s['loaded']
    assert all(r['accounting']['scope'].startswith('task_real:') for r in rs)
    paired=dict(complete_pairs=True,N_families=4,conditions={'Full':{'both_correct_families':2}},Delta_F1=.10,
                pairs=[dict(delta=.2,valid_both_conditions=True)]*2)
    assert not t.scientific_gate(p,rs,d.ledger,paired,[p[0]['family']])['passed']
    # labels identify path; this run's manifest must remain model_calls=0.
    damaged=copy.deepcopy(rs);damaged[0]['slots'][0]['speaker']='Bob'
    assert not t.engineering_complete(p,damaged,d.ledger,require_real=True)['passed']


@pytest.mark.parametrize('fault',['missing','wrong_count','drift'])
def test_T12_task_adapter_unknown_usage_count_identity(task_driver,fault):
    d,s,p,v=task_driver
    if fault=='drift':
        d.begin(p[0]['id']);d.generate(Agent(v[p[0]['family']][0]).request(0),p[0]['id'],0);s['drift']=True
        with pytest.raises(SafetyError):d.generate(Agent(v[p[0]['family']][1]).request(1),p[0]['id'],1)
        d.abort(p[0]['id'],'synthetic-drift') if not s['drift'] else d.ledger.fence('synthetic-drift')
    else:
        s[fault]=True;rs=run_campaign(p,v,lambda row:d,lambda *a:None)
        assert len(rs)==1 and not rs[0]['completed']
    assert d.ledger.state['fenced']
    assert d.ledger.state['http']['generation']<2


def test_T13_scoring_does_not_substitute_engineering(tmp_path):
    p,v=setup();families=list(v)
    fake=dict(started=True,completed=False,finals={'Alice':parse_output(outputs()[4],'Alice','local_final',{}),'Bob':parse_output(outputs()[5],'Bob','local_final',{})})
    rows={f:{c:score_episode(fake,'SECRET_ALICE_FINAL') for c in ('Full','No-A2A')} for f in families}
    paired=paired_summary(families,rows);assert paired['complete_pairs']
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        assert not t.scientific_gate(p,[],l,paired,[families[0]])['passed']


def test_T14_plan_order_and_alias_refuse(tmp_path):
    p,v=setup();bad=copy.deepcopy(p);bad[1]['id']=bad[0]['id']
    with pytest.raises(SafetyError):t.validate_plan(bad)
    with t.TaskLedger(tmp_path/'b',p,fixture=True) as l:
        d=t.TaskFixtureDriver(l,outputs())
        with pytest.raises(SafetyError):d.begin(p[1]['id'])


def test_T15_literal_prompt_frozen_and_probe_caps_intact():
    assert hashlib.sha256((t.ROOT/'extensions/masbench_reasoning/fair_final_v2_prompt.txt').read_bytes()).hexdigest()==t.TEMPLATE_SHA
    assert t.probe.CAPS['generation']==2 and sum(t.CAPS.values())==440
    assert t.probe.SCOPE!=t.SCOPE and t.probe.AUTH!=t.AUTH


def test_T16_no_cache_or_scoring_in_task_orchestrator():
    import ast
    from extensions.masbench_reasoning import fair_final_v2_task_campaign as c
    tree=ast.parse(Path(c.__file__).read_text())
    imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any('scoring' in x or 'evaluation' in x for x in imports)
