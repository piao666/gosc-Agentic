"""Independent stdlib task-profile evidence audit; no production/scoring imports."""
import hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path
BASE='c0621a1ab2cc249bbb6acb3b81cf1cec14591bcd'
ROOT=Path(__file__).resolve().parents[1]
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def dig(v):return hashlib.sha256(canonical(v)).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    from scripts.hpc_runs import require_hpc
    require_hpc();start=time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('audit120')));signal.alarm(120)
    runid=os.environ['T3RVT_CONTRACT_RUN'];assert runid.startswith('hpc-t3rv2i-task-contract-')
    run=ROOT/'research/sync/runs'/runid;report=json.loads((run/'outputs/contract.json').read_bytes())
    assert json.loads((run/'status.json').read_bytes())['status']=='completed' and report['passed']
    assert all(report['labels'][f'T{i:02d}'] for i in range(1,17))
    assert all(report[k]==0 for k in ('model_calls','real_HTTP','real_helper_calls','service_switches','real_task_records_read'))
    for name,h in report['source_files'].items():assert sha(ROOT/name)==h
    inv=json.loads((run/'outputs/hdd_inventory.json').read_bytes());root=Path(inv['root'])
    assert root==Path('/hdd/u202520081000097/gosc-t3rv2t-contracts')/runid
    for e in inv['files']:
        p=root/e['path'];assert not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
    assert sum(r['bytes'] for r in inv['files'])<=64*1024**2
    data=json.loads((run/'outputs/task_fixture.json').read_bytes());plan=data['plan'];rs=data['results']
    assert len(plan)==len(rs)==8 and len({r['family'] for r in plan})==4
    prev='0'*64;requests={};finished={};http={};cleanup={};starts=[];sourceSHA=[]
    for i,line in enumerate((Path(data['budget_root'])/'ledger.jsonl').read_bytes().splitlines()):
        row=json.loads(line);h=row.pop('hash');assert row['seq']==i and row['previous']==prev and dig(row)==h;prev=h
        e=row['event'];k=e['kind']
        if k=='request':assert e['id'] not in requests;requests[e['id']]=e
        if k=='finish':assert e['id'] in requests;finished[e['id']]=e
        if k=='v2-http':
            assert e['fake_operation'] is True;http[e['category']]=http.get(e['category'],0)+1
        if k=='episode' and e['status']=='started':starts.append(e['id'])
        if k=='v2-cleanup':cleanup[e['episode']]=e['status']
        if k=='bytes':assert sha(Path(data['budget_root'])/'artifacts'/e['path'])==e['sha256']
    assert len(requests)==len(finished)==48 and starts==[p['id'] for p in plan]
    # Separately inspect the real-adapter path under FakeRPC. In the red run,
    # unknown cleanup events produced a duplicate sequence; never conceal it.
    live_journals=[e for e in inv['files'] if 'test_T11_' in e['path'] and e['path'].endswith('hdd/fixture/budget/ledger.jsonl')]
    assert len(live_journals)==1
    prev_live='0'*64;live_req={};live_clean={}
    for i,line in enumerate((root/live_journals[0]['path']).read_bytes().splitlines()):
        row=json.loads(line);h=row.pop('hash');assert row['seq']==i and row['previous']==prev_live and dig(row)==h;prev_live=h
        e=row['event']
        if e['kind']=='request':live_req[e['id']]=e
        if e['kind']=='cleanup':live_clean[e['episode']]=e['status']
    assert len(live_req)==48 and len(live_clean)==8 and set(live_clean.values())=={'verified'}
    assert sum(e['output'] for e in requests.values())==24576
    assert http['get']==152 and http['generation']==48 and http['render']==48 and http['unload']==8
    assert all(e['status']=='completed' and e['usage'] is not None and not e['uncertain'] for e in finished.values())
    for p,r in zip(plan,rs):
        assert r['id']==p['id'] and r['completed'] and r['error'] is None
        assert cleanup[r['id']]=='verified-fixture-only' and r['accounting']['scope'].startswith('task_fixture:')
        assert len(r['slots'])==6 and len(r['finals'])==2
        for i,s in enumerate(r['slots']):
            assert s['turn']==i and s['speaker']==('Alice' if i%2==0 else 'Bob') and s['status']=='returned'
            assert hashlib.sha256(json.dumps(s['request'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==s['request_sha256']
            assert s['client_audit']['usage']['prompt_tokens']==requests[r['id']+'/t'+str(i)]['input']
        assert 'SECRET_ALICE_FINAL' not in str(r['slots'][5]['request'])
        assert 'SECRET_BOB_FINAL' not in str(r['slots'][4]['request'])
        assert len(r['slots'][0]['request'])==3
        if p['condition']=='No-A2A':assert r['received_sources']==[{},{}]
        else:
            assert len(r['messages'])==4 and all(m['delivered'] for m in r['messages'])
            for m in r['messages']:
                src=m['source'];slot=r['slots'][src['turn']]
                assert src['request_sha256']==slot['request_sha256'] and src['response_sha256']==slot['client_audit']['response_sha256']
    frozen=['application.py','evaluation.py','fair_final_v2.py','fair_final_v2_prompt.txt','fair_final_v2_scoring.py','fair_final_v2_guard.py','fair_final_v2_live.py','execution_safety.py','client.py','live_driver.py','wire.py']
    unchanged={}
    for name in frozen:
        rel='extensions/masbench_reasoning/'+name
        before=subprocess.check_output(['git','show',BASE+':'+rel]);assert hashlib.sha256(before).hexdigest()==sha(ROOT/rel);unchanged[rel]=sha(ROOT/rel)
    for rel in ['experiments_ext/masbench_t3rv2_live_probe.py','research/protocols/masbench_t3rv2_live_authorization_2026-11-26.json']:
        before=subprocess.check_output(['git','show',BASE+':'+rel]);assert hashlib.sha256(before).hexdigest()==sha(ROOT/rel);unchanged[rel]=sha(ROOT/rel)
    result=dict(passed=True,contract_run=runid,fixture_requests_independently_reconstructed=48,episodes=8,families=4,source_files=report['source_files'],unchanged=unchanged,model_calls=0,actual_task_ability='not tested',elapsed_seconds=time.monotonic()-start)
    Path(os.environ['GOSC_OUTPUT_DIR'],'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

