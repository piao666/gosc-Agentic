"""Ordered, restart-resistant HPC reproduction queue using unmodified original code."""
from pathlib import Path
import argparse
import hashlib
import gzip
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time

from hpc_runs import ROOT,require_hpc,write_json,resource_limits
from hpc_reproduce import snapshot,copy_environment

WORK=ROOT/'.local/ordered-reproduction-20261019'
PLAN=ROOT/'research/protocols/ordered_reproduction_v1.json'
# Order is deliberately explicit. Original calibration is separately unavailable.
STAGES=[
    ('selection','repro_selection',['--mode','select'],120,21600),
    ('selection-fresh','repro_selection',['--mode','fresh'],120,3600),
    ('c-frontier','experiments.run_revision',['--only','frontier','--seeds','100','--workers','2'],120,21600),
    ('c-where','experiments.run_revision',['--only','where_tom','--seeds','100','--workers','2'],120,21600),
    ('c-belief','experiments.run_belief_divergence',['--seeds','100','--workers','2'],120,10800),
    ('c-analysis','repro_extra',['--mode','matched'],120,3600),
    ('radio-noise','experiments.run_realistic',['--only','noise','--seeds','100','--workers','2'],120,43200),
    ('radio-overhead','experiments.run_realistic',['--only','overhead','--seeds','100','--workers','2'],120,86400),
    ('radio-shared','experiments.run_realistic',['--only','shared','--seeds','100','--workers','2'],120,43200),
    ('radio-fresh','experiments.validate_realistic',['--only','noise','overhead','shared','--workers','2'],120,21600),
    ('main-sweeps','experiments.run_all',['--seeds','100','--workers','2'],120,21600),
    ('revision-rest','experiments.run_revision',['--only','ablation','private','downlink','fbl','rescue','filtered_periodic','suppress_periodic','genie_ref','rate_aware','--seeds','100','--workers','2'],120,43200),
    ('joint','experiments.run_joint',['--seeds','100'],1800,21600),
    ('scheduler','experiments.analyze_scheduler',['--seeds','30'],1800,14400),
    ('theory','experiments.analyze_theory',['--seeds','30','--workers','2'],1800,14400),
    ('value-fidelity','experiments.diagnose_value',['--missions','20','--every','8','--reps','12','--first_seed','2000'],1800,21600),
    ('fidelity-analysis','experiments.analyze_fidelity',[],1800,3600),
    ('cached-llm','repro_extra',['--mode','cached'],120,10800),
    ('live-llm','repro_extra',['--mode','live'],1800,86400),
    ('sensitivity','repro_selection',['--mode','sensitivity'],120,10800),
    ('sensitivity-fresh','repro_selection',['--mode','sensitivity-fresh'],120,3600),
    ('genie-fresh','repro_selection',['--mode','genie'],120,3600),
    ('final-replot','repro_extra',['--mode','replot'],1800,7200),
]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run_legacy(work,module,arguments,timeout,job_timeout):
    env=os.environ.copy();env['REPRO_PROJECT_ROOT']=str(ROOT)
    env['PYTHONPATH']=str(ROOT/'scripts')+os.pathsep+str(work)
    env['MPLCONFIGDIR']=str(Path(os.environ['GOSC_OUTPUT_DIR'])/'mplconfig')
    command=[sys.executable,str(ROOT/'scripts/repro_legacy.py'),'--workspace',str(work),'--module',module,'--job-timeout',str(job_timeout),'--',*arguments]
    child=subprocess.Popen(command,cwd=work,env=env,start_new_session=True)
    try:
        code=child.wait(timeout=timeout)
        if code:raise RuntimeError(f'Original entry point exit {code}')
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        raise


def stage(name):
    require_hpc();entry=next(x for x in STAGES if x[0]==name)
    out=Path(os.environ['GOSC_OUTPUT_DIR']);before=snapshot();copy_environment(out)
    source=json.loads((ROOT/'.local/hpc-sync/latest_manifest.json').read_text())
    for item in source['files']:assert digest(ROOT/item['path'])==item['remote_sha256'],item['path']
    inventory={p.name:digest(p) for p in (WORK/'results').glob('*') if p.is_file()}
    write_json(out/'stage_plan.json',{'stage':name,'module':entry[1],'arguments':entry[2],
        'job_timeout_seconds':entry[3],'stage_timeout_seconds':entry[4],'workers':2,
        'numeric_threads':1,'workspace':str(WORK),'plan_sha256':digest(PLAN),
        'input_result_hashes':inventory,'source_sync_id':source['sync_id'],
        'known_unpooled_original_calls':2 if name=='main-sweeps' else 0})
    def interrupted(signum,frame):raise KeyboardInterrupt('Stage interrupted')
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,interrupted)
    fresh_expected=None
    if name=='radio-fresh':
        sys.path.insert(0,str(WORK))
        from repro_fresh_plan import plan as fresh_plan
        fresh_expected=fresh_plan(WORK)
        assert fresh_expected['missions']<=10300
        write_json(out/'fresh_job_plan.json',fresh_expected)
    succeeded=False
    try:
        run_legacy(WORK,entry[1],entry[2],entry[4],entry[3]);succeeded=True
    finally:
        derived=[]
        for p in (WORK/'results').glob('*'):
            if p.is_file() and inventory.get(p.name)!=digest(p):
                destination=out/'legacy_results'/p.name;destination.parent.mkdir(exist_ok=True)
                shutil.copyfile(p,destination);derived.append({'name':p.name,'sha256':digest(p)})
        after=snapshot();write_json(out/'input_integrity.json',{'before':before,'after':after,'unchanged':before==after})
        write_json(out/'legacy_outputs.json',{'stage_returned_normally':succeeded,'changed_result_files':derived})
        if before!=after:raise RuntimeError('Protected original inputs changed')
    audit_events(out)
    if fresh_expected is not None:
        from repro_fresh_plan import audit as fresh_audit
        write_json(out/'fresh_plan_audit.json',fresh_audit(out,fresh_expected))
    compare_results(out)


def equal(a,b):
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        return (math.isnan(a) and math.isnan(b)) or math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
    return a==b


def compare_results(out):
    from repro_compare import compare_file
    reports=[]
    for p in (out/'legacy_results').glob('*'):
        if p.suffix not in ['.json','.jsonl']:continue
        original=ROOT/'results'/p.name
        if not original.exists():original=original.with_name(original.name+'.gz')
        if not original.exists():reports.append({'file':p.name,'status':'no_original_file_for_this_derived_product'});continue
        reports.append(compare_file(p,original))
    write_json(out/'original_comparison.json',{'scope':'Explicit identity and coverage; no hidden replacement or rerun on differences','files':reports})
    if any(row.get('status')=='invalid_identity' for row in reports):
        raise RuntimeError('Historical comparison identity is invalid; preserve outputs and inspect coverage')


def audit_events(out):
    starts=ends=0;maximum=0;raw_results=0
    for p in out.glob('pool-*-events.jsonl'):
        active=set()
        for line in p.read_text().splitlines():
            row=json.loads(line);key=row['index']
            if row['event']=='start':
                assert key not in active;active.add(key);starts+=1;maximum=max(maximum,len(active));assert len(active)<=2
            else:assert key in active;active.remove(key);ends+=1;assert row['status']=='completed'
        assert not active
    for p in out.glob('pool-*-jobs.jsonl'):
        for line in p.read_text().splitlines():
            row=json.loads(line);assert row['status']=='completed';raw_results+=1
    assert starts==ends==raw_results
    write_json(out/'stage_audit.json',{'status':'verified','worker_starts':starts,'worker_terminals':ends,
        'raw_original_job_results':raw_results,'max_concurrency':maximum,'protected_inputs_unchanged':True,
        'scope':'Bookkeeping and lifecycle; historical scientific comparisons are recorded separately'})


def pipeline():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR']);run_dir=Path(os.environ['GOSC_RUN_DIR'])
    plan=json.loads(PLAN.read_text());assert plan['source_head']=='876fc523b113b3b65e19f0b730f1573ccc2ee17f'
    assert plan['workers']==2 and plan['stages']==[x[0] for x in STAGES]
    limits=resource_limits();assert int(limits['cpu_quota'])/int(limits['cpu_period'])>=2
    assert int(limits['memory_bytes'])>=25769803776
    if WORK.exists():raise RuntimeError('Workspace already exists; inspect existing state rather than silently restart')
    WORK.mkdir()
    for folder in ['gosc','experiments']:
        shutil.copytree(ROOT/folder,WORK/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (WORK/'results/llm_cache').mkdir(parents=True)
    for p in (ROOT/'results/llm_cache').glob('*.jsonl'):shutil.copyfile(p,WORK/'results/llm_cache'/p.name)
    status={'status':'running','stages':[{'stage':s[0],'status':'pending'} for s in STAGES],
        'calibration':'upstream_procedure_not_provided_at_verified_commit387b493',
        'source_plan_sha256':digest(PLAN),'workers':2,'started_at':time.time(),'live_phase_requires_existing_service':True}
    write_json(out/'pipeline_status.json',status);start=time.monotonic();cancel={'requested':False}
    def interrupted(signum,frame):cancel['requested']=True
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,interrupted)
    try:
        for record,entry in zip(status['stages'],STAGES):
            if cancel['requested'] or time.monotonic()-start>=plan['global_timeout_seconds']:raise KeyboardInterrupt('Pipeline stopped or global budget exhausted')
            name=entry[0];run_id='ordered-'+name+'-20261019';record.update(status='running',run_id=run_id,started_at=time.time())
            write_json(out/'pipeline_status.json',status)
            command=[sys.executable,str(ROOT/'scripts/hpc_runs.py'),'run','--run-id',run_id,'--kind',
                'analysis' if name in ['c-analysis','fidelity-analysis','final-replot'] else 'simulation',
                '--stage','ordered-'+name,'--purpose','User-authorized ordered original reproduction: '+name,
                '--config',str(PLAN.relative_to(ROOT)),'--cache-mode','cache_only_no_http' if name=='cached-llm' else 'not_applicable',
                '--','{python}',str(ROOT/'scripts/repro_ordered.py'),'stage','--name',name]
            with (out/(name+'.launch.log')).open('wb') as log:
                child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                while child.poll() is None:
                    if cancel['requested'] or time.monotonic()-start>=plan['global_timeout_seconds']:
                        path=ROOT/'research/sync/runs'/run_id/'status.json'
                        if path.exists():
                            pid=json.loads(path.read_text()).get('pid')
                            if pid:
                                try:os.killpg(pid,signal.SIGTERM)
                                except ProcessLookupError:pass
                        child.wait(timeout=20);raise KeyboardInterrupt('Pipeline interrupted')
                    active=ROOT/'research/sync/runs'/run_id/'outputs/active_pool.json'
                    if active.exists():
                        try:record['progress']=json.loads(active.read_text())
                        except json.JSONDecodeError:pass
                    record['updated_at']=time.time();write_json(out/'pipeline_status.json',status);time.sleep(3)
            record.update(status='completed' if child.returncode==0 else 'failed',exit_code=child.returncode,finished_at=time.time())
            write_json(out/'pipeline_status.json',status)
            # Missing live runtime or incomplete published caches is an explicit external
            # constraint; independent later sensitivity work can still execute.
            if child.returncode and name not in ['cached-llm','live-llm']:raise RuntimeError('Stage failed: '+name)
        status['status']='completed_available_procedures_with_documented_gaps'
    except KeyboardInterrupt:
        status['status']='interrupted';raise
    except BaseException:
        status['status']='failed';raise
    finally:
        status['finished_at']=time.time();write_json(out/'pipeline_status.json',status)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    sub.add_parser('pipeline');q=sub.add_parser('stage');q.add_argument('--name',choices=[s[0] for s in STAGES],required=True)
    args=p.parse_args()
    if args.mode=='pipeline':pipeline()
    else:stage(args.name)


if __name__=='__main__':main()
