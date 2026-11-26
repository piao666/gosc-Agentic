"""Independent stdlib audit. Does not import live driver/parser/scorer."""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
RUN='hpc-t3rv2i-live-probe-20261126'
MODEL='qwen2.5:7b'
MANIFEST='845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'
TEMPLATE='eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175'
WEIGHT='2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730'
CAPS=dict(generation=2,render=2,get=8,cleanup_get=14,unload=2,lifecycle_get=128)


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()


def main():
    from scripts.hpc_runs import require_hpc
    require_hpc();begin=time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('audit120')));signal.alarm(120)
    run=ROOT/'research/sync/runs'/RUN
    state=json.loads((run/'status.json').read_bytes());assert state['status']=='completed'
    inv=json.loads((run/'outputs/hdd_inventory.json').read_bytes())
    base=Path(inv['root']);assert base==Path('/hdd/u202520081000097/gosc-t3rv2-live')/RUN
    for row in inv['files']:
        p=base/row['path'];assert not p.is_symlink() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    assert sum(r['bytes'] for r in inv['files'])<=128*1024**2
    summary=json.loads((base/'summary.json').read_bytes());assert summary['passed'] and summary['error'] is None
    a=json.loads((ROOT/'research/protocols/masbench_t3rv2_live_authorization_2026-11-26.json').read_bytes())
    assert a['approved'] is True and a['run_id']==RUN and a['generation_cap']==2 and a['task_generation_cap']==0
    assert a['monitoring_approved'] is True
    for p,h in a['bound_files'].items():assert sha(ROOT/p)==h
    assert sha(ROOT/a['contract_receipt'])==a['contract_sha256']
    contract=json.loads((ROOT/a['contract_receipt']).read_bytes());assert contract['passed'] and contract['model_calls']==0
    assert all(contract['labels'][f'D{i:02d}']>0 for i in range(1,13))
    for p,h in contract['source_files'].items():assert a['bound_files'][p]==h
    post_deadline=sys.argv[1:]==['--post-deadline-review']
    assert not sys.argv[1:] or post_deadline
    deadline_met=True;wall_since_start=None
    events=[];previous='0'*64;http=dict.fromkeys(CAPS,0);ops=dict(counter=0,start=0,stop=0)
    reservations={};finishes={};cleanup={};sent=set();resource_gaps=[];last_active=None
    for index,line in enumerate((base/'budget/ledger.jsonl').read_bytes().splitlines()):
        row=json.loads(line);h=row.pop('hash')
        assert row['seq']==index and row['previous']==previous and digest(row)==h
        previous=h;e=row['event'];events.append(e);k=e['kind']
        if k=='init':
            wall_since_start=time.monotonic()-e['started_mono']
            deadline_met=wall_since_start<2000
            if not post_deadline:assert deadline_met
        if k=='request':
            assert e['id'] not in reservations and e['output']==512 and 0<=e['input']<=15872
            reservations[e['id']]=e
        if k=='finish':assert e['id'] in reservations;finishes[e['id']]=e
        if k=='operation':ops[e['name']]+=1
        if k=='http':
            assert e['live_operation'] is True;http[e['category']]+=1
            if e['category']=='generation':
                assert e['request_id'] in reservations and e['request_id'] not in sent;sent.add(e['request_id'])
        if k=='cleanup':cleanup[e['episode']]=e['status']
        if k=='bytes':assert sha(base/'budget/artifacts'/e['path'])==e['sha256']
        if k=='control' and e['label']=='monitor-bind':last_active=None
        if k=='control' and e['label']=='resources':
            v=e['values'];assert v['driver_rss']<=2*1024**3 and v['service_rss']<=16*1024**3 and v['gpu_bytes']<=16*1024**3
            if e['enforced_active']:
                if last_active is not None:resource_gaps.append(e['sample_start']-last_active)
                last_active=e['sample_start']
            else:last_active=None
    assert http==summary['http'] and all(http[k]<=CAPS[k] for k in CAPS) and sum(http.values())<=156
    assert http['generation']==2 and http['render']==2 and http['unload']==2
    assert ops==dict(counter=2,start=2,stop=2)==summary['operations']
    assert len(reservations)==len(finishes)==2 and all(e['status']=='completed' and e['usage'] is not None and not e['uncertain'] for e in finishes.values())
    assert cleanup==dict.fromkeys(['deploy-short','deploy-long'],'verified')
    assert resource_gaps and max(resource_gaps)<=.5 and summary['monitor']['max_active_sample_start_gap_seconds']<=.5
    controls=[e for e in events if e['kind']=='control']
    assert any(e['label']=='weight-SHA-verified' and e['sha256']==WEIGHT for e in controls)
    assert len([e for e in controls if e['label']=='rollback-verified'])==1
    assert len([e for e in controls if e['label']=='exit-barrier'])==2
    inputs=json.loads((ROOT/'research/logs/masbench-t3rv2-deployment-2026-11-26/probe_inputs.json').read_bytes())['cases']
    findings=[]
    for case in inputs:
        key=case['id'];art=base/'budget/artifacts'/key
        counted=json.loads((art/'count.json').read_bytes());reply=counted['reply'];cr=reply['requests'][0]
        assert counted['messages']==case['messages'] and reply['vocab_only'] is True and reply['tensor_context_created'] is False
        assert reply['template_sha256']==TEMPLATE and reply['add_special'] is False and reply['parse_special'] is True
        assert len(cr['token_ids'])==cr['token_count'] and digest(cr['token_ids'])==cr['token_ids_json_sha256']
        assert hashlib.sha256(cr['rendered'].encode()).hexdigest()==cr['rendered_sha256']
        binding=json.loads((art/'binding.json').read_bytes());assert binding['debug']['_debug_info']['rendered_template']==cr['rendered']
        assert binding['ps']['models'][0]['digest']==MANIFEST and binding['ps']['models'][0]['context_length']==16384
        assert binding['version']['version']=='0.11.11'
        ready=json.loads((art/'client-request_ready.json').read_bytes())['data']
        done=json.loads((art/'client-completed.json').read_bytes())['data']
        assert ready['messages']==case['messages'] and ready['request_sha256']==digest(case['messages'])
        assert ready['prompt_tokens_preflight']==cr['token_count']==done['usage']['prompt_tokens']
        assert done['usage']['completion_tokens']<=512 and not done['usage_missing'] and done['error'] is None
        assert done['finish_reason']=='stop' and done['response']['model']==MODEL
        assert cr['token_count']+512<=16384
        if key=='deploy-long':assert cr['token_count']>1024
        raw=done['response']['choices'][0]['message']['content']
        normalized=(raw or '').replace('\r\n','\n').strip(' \t\r\n')
        lines=normalized.split('\n')
        valid=(lines[0]=='Alice: MESSAGE' and 2<=len(lines)<=5 and all(re.fullmatch(r'<([QR])>[^<>\x00-\x1f\x7f]+</\1>',x) for x in lines[1:]) and len(normalized.encode())<=4096)
        findings.append(dict(id=key,prompt_tokens=cr['token_count'],completion_tokens=done['usage']['completion_tokens'],
                             format_valid=bool(valid),raw_sha256=hashlib.sha256((raw or '').encode()).hexdigest()))
    assert not (ROOT/'.local/ollama/context_profile.json').exists() and (ROOT/'.local/t1-service.lock').stat().st_size==0
    restored=summary['restored'];pid=json.loads((ROOT/'.local/ollama/service.json').read_bytes())['pid']
    assert pid==restored['service_pid']
    fields=Path('/proc',str(pid),'stat').read_text().rsplit(') ',1)[1].split()
    assert fields[19]==restored['service_stamp'] and fields[0]!='Z'
    env=dict(x.split(b'=',1) for x in Path('/proc',str(pid),'environ').read_bytes().split(b'\0') if b'=' in x)
    assert env[b'OLLAMA_CONTEXT_LENGTH']==b'1024' and env[b'OLLAMA_NUM_PARALLEL']==b'1'
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],timeout=3,text=True)
    assert all(int(x)==0 for x in gpu.splitlines())
    report=dict(passed=True,scope='two immutable artificial deployment probes; not task capability',
        run_id=RUN,http=http,observed_HTTP_send_markers=sum(e['label']=='http-sent' for e in controls),
        operations=ops,generations=2,task_generations=0,findings=findings,
        journals=len(events),HDD_files_verified=len(inv['files']),observed_peaks=summary['monitor']['peaks'],
        max_reconstructed_active_sample_gap_seconds=max(resource_gaps),hard_resource_isolation=False,
        effective_context=16384,rollback_context=1024,lease_empty=True,current_GPU_MiB=0,
        elapsed_seconds=time.monotonic()-begin,raw_HDD_root=str(base),
        review_mode='separately resumed post-deadline offline audit' if post_deadline else 'original deadline',
        original_continuous_2000s_closeout_met=deadline_met,wall_since_original_start=wall_since_start)
    out=Path(os.environ['GOSC_OUTPUT_DIR']);(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));signal.alarm(0)


if __name__=='__main__':main()
