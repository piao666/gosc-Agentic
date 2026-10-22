"""Explicit resume of the original ordered campaign, preserving completed runs."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from hpc_runs import ROOT,require_hpc,write_json,resource_limits
from repro_ordered import WORK,PLAN,STAGES,digest

FIRST=['selection','selection-fresh','c-frontier','c-where']
ORIGINAL_PLAN_SHA='5c815468e8616e40f8d5e6c0cd9af6751626bc91f79132603602bd5c72a02c2b'

def validate_state(root,work,now=None):
    """Fail closed on changed science inputs, missing outputs or non-prefix completion."""
    runroot=root/'research/sync/runs'
    original=json.loads((runroot/'hpc-ordered-queue-20261019/status.json').read_text())
    if original['status']!='failed':raise RuntimeError('Expected preserved failed predecessor')
    start=datetime.fromisoformat(original['started_at']).timestamp()
    deadline=start+259200
    if (time.time() if now is None else now)>=deadline:raise RuntimeError('Original 72h deadline exhausted')
    if digest(root/'research/protocols/ordered_reproduction_v1.json')!=ORIGINAL_PLAN_SHA:raise RuntimeError('Frozen original plan changed')
    verified={}
    for folder in ['gosc','experiments']:
        for p in sorted((root/folder).rglob('*.py')):
            rel=p.relative_to(root)
            if not (work/rel).is_file() or digest(p)!=digest(work/rel):raise RuntimeError('Workspace source differs: '+str(rel))
            verified[str(rel)]=digest(p)
    for p in sorted((root/'results/llm_cache').glob('*.jsonl')):
        q=work/'results/llm_cache'/p.name
        if not q.is_file() or digest(p)!=digest(q):raise RuntimeError('Published replay cache changed')
    done=[];pending=[];last={};seen_pending=False
    for name,*_ in STAGES:
        rid=('ordered-'+name+'-20261019') if name in FIRST else ('resume-'+name+'-20261020')
        path=runroot/rid
        if path.exists():
            state=json.loads((path/'status.json').read_text())
            if state['status']!='completed' or state['exit_code']!=0:raise RuntimeError('Existing resume run not completed: '+rid)
            if seen_pending:raise RuntimeError('Completed stages are not a contiguous prefix')
            manifest=json.loads((path/'artifacts.json').read_text())
            for item in manifest['files']:
                target=path/item['path']
                if not target.is_file() or digest(target)!=item['sha256']:raise RuntimeError('Closed artifact changed: '+str(target))
            derived=json.loads((path/'outputs/legacy_outputs.json').read_text())
            for item in derived['changed_result_files']:last[item['name']]=item['sha256']
            done.append({'stage':name,'run_id':rid,'status_sha256':digest(path/'status.json'),'artifacts_sha256':digest(path/'artifacts.json')})
        else:
            if name in FIRST:raise RuntimeError('Missing completed predecessor '+name)
            seen_pending=True;pending.append({'stage':name,'run_id':rid})
    for name,sha in last.items():
        if not (work/'results'/name).is_file() or digest(work/'results'/name)!=sha:raise RuntimeError('Workspace result differs: '+name)
    failed=runroot/'ordered-c-belief-20261019'
    if json.loads((failed/'status.json').read_text())['status']!='failed':raise RuntimeError('Failed original record changed')
    if list((failed/'outputs').glob('pool-*-jobs.jsonl')):raise RuntimeError('Original failed belief run contains jobs; inspect before retry')
    return {'completed_prefix':done,'pending':pending,'original_started_at':original['started_at'],
      'original_deadline_epoch':deadline,'remaining_wall_seconds':deadline-(time.time() if now is None else now),
      'source_plan_sha256':ORIGINAL_PLAN_SHA,'workspace_source_hashes':verified,'workspace_result_hashes':last,
      'workspace':str(work),'scientific_status':'Historical differences retained, not a scientific equivalence pass',
      'diagnostic_runs':['hpc-difference-probe-20261020','hpc-numpy-diagnosis-relay-20261020'],
      'unresolved':'All historical C/selection differences are not explained; current environment remains pinned',
      'workers':2,'numeric_threads':1,'no_new_method_training':True}

def trace_diagnostics(out):
    primary=ROOT/'research/sync/runs/hpc-difference-probe-20261020/outputs'
    numpy=ROOT/'research/sync/runs/hpc-numpy-diagnosis-relay-20261020/outputs'
    rows=[]
    for variant,folder in [('default-repeat2',primary),('scalar-exp',primary),('no-simd',primary),('numpy-1.26.4',numpy),('numpy-2.2.6',numpy)]:
        for i in range(6):
            a=json.loads((primary/f'trace-default-repeat1-{i}.json').read_text())
            path=folder/f'trace-{variant}-{i}.json'
            if not path.exists():continue
            b=json.loads(path.read_text());changed=None
            for j,(x,y) in enumerate(zip(a,b)):
                if x['chosen']!=y['chosen']:
                    changed={'decision_index':j,'current_choice':x['chosen'],'variant_choice':y['chosen'],
                       'same_options_except_values':[[{k:v for k,v in z.items() if k!='value_hex'} for z in g] for g in x['options']]==[[{k:v for k,v in z.items() if k!='value_hex'} for z in g] for g in y['options']],
                       'current_options':x['options'],'variant_options':y['options']};break
            rows.append({'variant':variant,'case_index':i,'current_decisions':len(a),'variant_decisions':len(b),'first_choice_difference':changed})
    write_json(out/'trace_divergence.json',rows)

def main():
    require_hpc();ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['preflight','resume']);ap.add_argument('--through',choices=[s[0] for s in STAGES]);args=ap.parse_args()
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    limits=resource_limits()
    if float(limits['cpu_quota'])/float(limits['cpu_period'])<2 or int(limits['memory_bytes'])<25769803776:raise RuntimeError('Expected resource allocation unavailable')
    plan=validate_state(ROOT,WORK);write_json(out/'resume_manifest.json',plan)
    trace_diagnostics(out)
    if args.mode=='preflight':print(json.dumps({'verified_completed':len(plan['completed_prefix']),'pending':len(plan['pending']),'remaining_wall_seconds':plan['remaining_wall_seconds']}));return
    status={'status':'running','skipped_completed':plan['completed_prefix'],'stages':[],'original_deadline_epoch':plan['original_deadline_epoch']}
    write_json(out/'pipeline_status.json',status);cancel={'requested':False}
    def stop(signum,frame):cancel['requested']=True
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,stop)
    try:
        for item in plan['pending']:
            name=item['stage'];rid=item['run_id'];entry=next(s for s in STAGES if s[0]==name)
            if cancel['requested'] or time.time()>=plan['original_deadline_epoch']:raise KeyboardInterrupt('Original deadline or cancellation')
            row={**item,'status':'running','started_at':time.time()};status['stages'].append(row);write_json(out/'pipeline_status.json',status)
            command=[sys.executable,str(ROOT/'scripts/hpc_runs.py'),'run','--run-id',rid,'--kind','analysis' if name in ['c-analysis','fidelity-analysis','final-replot'] else 'simulation','--stage','resume-'+name,'--purpose','User-authorized continuation; retain historical differences: '+name,'--config',str(PLAN.relative_to(ROOT)),'--cache-mode','cache_only_no_http' if name=='cached-llm' else 'actual_http_new_cache' if name=='live-llm' else 'not_applicable','--','{python}',str(ROOT/'scripts/repro_ordered.py'),'stage','--name',name]
            with (out/(name+'.launch.log')).open('xb') as log:
                child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                while child.poll() is None:
                    if cancel['requested'] or time.time()>=plan['original_deadline_epoch']:
                        statepath=ROOT/'research/sync/runs'/rid/'status.json'
                        if statepath.exists():
                            pid=json.loads(statepath.read_text()).get('pid')
                            if pid:
                                try:os.killpg(pid,signal.SIGTERM)
                                except ProcessLookupError:pass
                        try:child.wait(timeout=25)
                        except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=5)
                        raise KeyboardInterrupt('Original global deadline/cancellation')
                    active=ROOT/'research/sync/runs'/rid/'outputs/active_pool.json'
                    if active.exists():
                        try:row['progress']=json.loads(active.read_text())
                        except json.JSONDecodeError:pass
                    row['updated_at']=time.time();write_json(out/'pipeline_status.json',status);time.sleep(3)
            row.update(status='completed' if child.returncode==0 else 'failed',exit_code=child.returncode,finished_at=time.time());write_json(out/'pipeline_status.json',status)
            if child.returncode and name not in ['cached-llm','live-llm']:raise RuntimeError('Stage failed: '+name)
            if args.through==name:break
        status['status']='completed_requested_prefix' if args.through else 'completed_available_procedures_with_documented_gaps'
    except KeyboardInterrupt:status['status']='interrupted';raise
    except BaseException:status['status']='failed';raise
    finally:status['finished_at']=time.time();write_json(out/'pipeline_status.json',status)

if __name__=='__main__':main()
