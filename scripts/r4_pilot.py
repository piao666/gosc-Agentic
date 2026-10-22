"""Bounded, HPC-only R4-A0 executor; original scientific modules stay unchanged."""
from pathlib import Path
import argparse
import csv
import dataclasses
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
import traceback

from hpc_runs import ROOT, require_hpc, write_json
from hpc_reproduce import snapshot, copy_environment

# An absolute script entry puts scripts/, not the repository, on sys.path.
sys.path.insert(0, str(ROOT))

PLAN = ROOT/'research/protocols/r4_plan_v1.json'
THREADS = ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']
EXPECTED_SETTINGS = [
    {'name':'search-W100','base_config':{},'arms':[
        {'scheme':'gosc','overrides':{'energy_price':1e-5}},
        {'scheme':'sem_raf','overrides':{'sem_interval':4,'filter_eps':0.02}},
        {'scheme':'genie','overrides':{}}]},
    {'name':'rescue-W100','base_config':{'task':'rescue','deadline_min':60,'deadline_max':180},'arms':[
        {'scheme':'gosc','overrides':{'energy_price':1e-4}},
        {'scheme':'sem_ras','overrides':{'sem_interval':2,'filter_eps':1.0}},
        {'scheme':'genie','overrides':{}}]},
]


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def expand_plan(plan):
    """Reject changes to the authorized seed/configuration/compute scope."""
    p = plan['pilot']
    if plan['head'] != '876fc523b113b3b65e19f0b730f1573ccc2ee17f':
        raise ValueError('Unexpected baseline HEAD')
    if p['seeds'] != list(range(9000,9010)) or p['settings'] != EXPECTED_SETTINGS:
        raise ValueError('Pilot settings/seeds exceed the predeclared scope')
    if (p['workers_max'],p['thread_limit'],p['per_episode_timeout_seconds'],p['campaign_budget_seconds'],p['planned_missions']) != (2,2,120,1200,60):
        raise ValueError('Pilot resource budget changed')
    from gosc import Config
    jobs = []
    for seed in p['seeds']:
        for scene in p['settings']:
            for arm in scene['arms']:
                cfg = Config().with_(**(scene['base_config'] | arm['overrides']))
                assert not cfg.llm_agents and not cfg.tom_oracle
                config = json.loads(json.dumps(dataclasses.asdict(cfg)))
                jobs.append({'job_id':f"{scene['name']}-{seed}-{arm['scheme']}",
                             'setting':scene['name'],'seed':seed,'scheme':arm['scheme'],
                             'config':config,'config_sha256':fingerprint(config)})
    if len(jobs)!=60 or len({j['job_id'] for j in jobs})!=60:
        raise ValueError('Unexpected duplicate/missing jobs')
    return jobs


def validate_payload(job, value):
    if value['job_id']!=job['job_id'] or value['config_sha256']!=job['config_sha256'] or value['config']!=job['config']:
        raise ValueError('Worker identity/config mismatch')
    result, c = value['result'], job['config']
    for name in ['completion_time','found','bits','symbols','dl_symbols','false_declarations']:
        if not isinstance(result[name],int) or isinstance(result[name],bool) or result[name]<0:
            raise ValueError('Invalid result integer: '+name)
    if not 0<result['completion_time']<=c['max_steps'] or not 0<=result['found']<=c['n_victims']:
        raise ValueError('Invalid mission horizon/found')
    if not isinstance(result['completed'],bool) or result['completed']!=(result['found']==c['n_victims']):
        raise ValueError('Inconsistent located completion flag')
    if len(result['curve'])!=c['max_steps'] or len(result['trajectories'])!=c['n_agents'] or len(result['victims'])!=c['n_victims']:
        raise ValueError('Incomplete raw curves/trajectories/world')
    if result['confirm_latency'] is not None and not math.isfinite(result['confirm_latency']):
        raise ValueError('Non-finite latency')
    if c['task']=='rescue':
        if not 0<=result['saved']<=c['n_victims'] or not 0<=result['lost']<=c['n_victims']:
            raise ValueError('Invalid rescue counts')
        if result['saved_fraction']!=result['saved']/c['n_victims']:
            raise ValueError('Inconsistent saved fraction')
    expected = fingerprint({'victims':result['victims'],'starts':[x[0] for x in result['trajectories']]})
    if value['world_start_sha256']!=expected:
        raise ValueError('Invalid initial-world fingerprint')


def worker(spec, destination):
    require_hpc()
    if ROOT not in spec.resolve().parents or spec.parent!=destination.parent:
        raise ValueError('Worker files must be in the project temporary area')
    for key in THREADS:os.environ[key]='1'
    import resource
    from gosc import Config, run_episode
    job = json.loads(spec.read_text())
    config = dict(job['config'])
    config['rates']=tuple(config['rates']);config['llm_agents']=tuple(config['llm_agents'])
    cfg = Config(**config)
    if cfg.llm_agents or fingerprint(job['config'])!=job['config_sha256']:
        raise ValueError('Invalid or LLM worker config')
    started=time.perf_counter()
    result=run_episode(cfg,job['scheme'],job['seed'],record_traj=True)
    elapsed=time.perf_counter()-started
    usage=resource.getrusage(resource.RUSAGE_SELF)
    value={**job,'result':result,'simulation_elapsed_seconds':elapsed,
           'world_start_sha256':fingerprint({'victims':result['victims'],'starts':[x[0] for x in result['trajectories']]}),
           'worker_resources':{'max_rss_kib':usage.ru_maxrss,'cpu_user_seconds':usage.ru_utime,
                               'cpu_system_seconds':usage.ru_stime,'scope':'Whole worker process including interpreter/imports',
                               'numeric_library_threads':1,'peak_gpu_memory':None}}
    validate_payload(job,value)
    write_json(destination,value)


def run_jobs(jobs,out,temp,command_factory,validator,workers,per_job_timeout,budget,
             cancel=lambda:False,stop_on_failure=True):
    """Subprocess isolation permits real per-job timeouts and process reaping."""
    if workers not in [1,2] or len({x['job_id'] for x in jobs})!=len(jobs):
        raise ValueError('Invalid worker count or duplicate job IDs')
    out.mkdir(parents=True,exist_ok=True);temp.mkdir(parents=True,exist_ok=False)
    states={j['job_id']:{'job_id':j['job_id'],'status':'planned','started_at':None,'elapsed_seconds':None} for j in jobs}
    active={};records=[];pending=list(jobs);started=time.monotonic();max_active=0;reason=None
    events=out/'events.jsonl';raw=out/'episodes.jsonl';logs=out/'worker_logs.jsonl'
    for path in [events,raw,logs]:path.touch(exist_ok=False)
    def append(path,value):
        with path.open('a',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def progress():
        write_json(out/'mission_status.json',{'jobs':list(states.values()),'max_active_workers':max_active,'stop_reason':reason})
    def finish(job,status,why=None,entry=None,payload=None):
        key=job['job_id'];row={**job,'execution_status':status,'reason':why,'attempt_started':entry is not None,
            'process_exit_code':entry['process'].returncode if entry else None,
            'process_elapsed_seconds':time.monotonic()-entry['start'] if entry else None,
            'command':entry['command'] if entry else None}
        if payload is not None:row['output']=payload
        if entry:
            entry['stdout'].close();entry['stderr'].close()
            append(logs,{'job_id':key,'stdout':entry['stdout_path'].read_text(errors='replace'),
                         'stderr':entry['stderr_path'].read_text(errors='replace')})
            if status!='completed' and entry['result'].is_file():row['invalid_or_partial_worker_output']=entry['result'].read_text(errors='replace')
        records.append(row);append(raw,row)
        states[key].update(status=status,reason=why,elapsed_seconds=row['process_elapsed_seconds'])
        append(events,{'event':'terminal','job_id':key,'status':status,'monotonic_seconds':time.monotonic()-started})
        progress()
        print(f"terminal {len(records)}/{len(jobs)} {key} {status}",flush=True)
    def terminate(entry):
        p=entry['process']
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired:p.kill();p.wait()
    progress()
    try:
        while pending or active:
            elapsed=time.monotonic()-started
            if cancel():reason=reason or 'interrupted'
            if elapsed>=budget:reason=reason or 'campaign_budget'
            if reason:
                for key,entry in list(active.items()):
                    terminate(entry);finish(entry['job'],'timeout' if reason=='campaign_budget' else 'interrupted',reason,entry);del active[key]
                for job in pending:finish(job,'timeout' if reason=='campaign_budget' else 'interrupted',reason+'_not_started')
                pending.clear();break
            while pending and len(active)<workers:
                job=pending.pop(0);key=job['job_id'];folder=temp/key;folder.mkdir()
                spec=folder/'job.json';result=folder/'result.json';write_json(spec,job)
                stdout_path=folder/'stdout.log';stderr_path=folder/'stderr.log'
                stdout=stdout_path.open('wb');stderr=stderr_path.open('wb')
                argv=[str(x) for x in command_factory(job,spec,result)]
                env=os.environ.copy();env.update({k:'1' for k in THREADS});env['PYTHONPATH']=str(ROOT)
                begin=time.monotonic()
                try:p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                except Exception:
                    stdout.close();stderr.close();raise
                entry={'job':job,'process':p,'start':begin,'command':argv,'result':result,
                       'stdout':stdout,'stderr':stderr,'stdout_path':stdout_path,'stderr_path':stderr_path}
                active[key]=entry;states[key].update(status='running',started_at=time.time(),pid=p.pid)
                max_active=max(max_active,len(active));append(events,{'event':'start','job_id':key,'pid':p.pid,'active':len(active),'monotonic_seconds':begin-started});progress()
            for key,entry in list(active.items()):
                p=entry['process'];code=p.poll()
                if code is None and time.monotonic()-entry['start']>=per_job_timeout:
                    terminate(entry);finish(entry['job'],'timeout','episode_timeout',entry);del active[key]
                    if stop_on_failure:reason='episode_timeout'
                elif code is not None:
                    status,why,payload='completed',None,None
                    try:
                        if code:raise RuntimeError('Worker exited '+str(code))
                        payload=json.loads(entry['result'].read_text());validator(entry['job'],payload)
                    except Exception as e:status,why='failed',repr(e)
                    finish(entry['job'],status,why,entry,payload if status=='completed' else None);del active[key]
                    if status!='completed' and stop_on_failure:reason='worker_failure'
            if pending or active:time.sleep(0.02)
    finally:
        # Also account for unstarted keys when the controller itself raises.
        for key,entry in list(active.items()):
            terminate(entry);finish(entry['job'],'interrupted','controller_exception',entry)
        seen={x['job_id'] for x in records}
        for job in jobs:
            if job['job_id'] not in seen:finish(job,'interrupted','controller_exception_not_started')
    return {'records':records,'elapsed_seconds':time.monotonic()-started,'max_active_workers':max_active,'stop_reason':reason}


def summarize(run,jobs,out,targets):
    import numpy as np
    records=run['records'];done=[r for r in records if r['execution_status']=='completed']
    groups=[];pairs=[]
    for setting in ['search-W100','rescue-W100']:
        task='search' if setting.startswith('search') else 'rescue';metric='completion_time' if task=='search' else 'saved_fraction'
        periodic='sem_raf' if task=='search' else 'sem_ras'
        indexed={scheme:{r['seed']:r['output']['result'] for r in done if r['setting']==setting and r['scheme']==scheme}
                 for scheme in ['gosc',periodic,'genie']}
        for scheme,values in indexed.items():
            rows=list(values.values())
            if not rows:continue
            groups.append({'setting':setting,'scheme':scheme,'n':len(rows),'metric':metric,
                'mean_outcome':float(np.mean([r[metric] for r in rows])),
                'located_completion_fraction':float(np.mean([r['completed'] for r in rows])),
                'mean_found':float(np.mean([r['found'] for r in rows])),
                'mean_false_declarations':float(np.mean([r['false_declarations'] for r in rows])),
                'mean_bits':float(np.mean([r['bits'] for r in rows])),
                'mean_uplink_symbols':float(np.mean([r['symbols'] for r in rows])),
                'mean_dl_symbols_base_model':float(np.mean([r['dl_symbols'] for r in rows]))})
        seeds=sorted(set.intersection(*(set(v) for v in indexed.values())))
        for seed in seeds:
            world={r['output']['world_start_sha256'] for r in done if r['setting']==setting and r['seed']==seed}
            if len(world)!=1:raise RuntimeError('Unpaired initial world: '+setting+'/'+str(seed))
        if seeds:
            g=np.array([indexed['gosc'][s][metric] for s in seeds]);p=np.array([indexed[periodic][s][metric] for s in seeds])
            gy=np.array([indexed['gosc'][s]['symbols'] for s in seeds],float);py=np.array([indexed[periodic][s]['symbols'] for s in seeds],float)
            idx=np.random.default_rng(0).integers(0,len(seeds),(4000,len(seeds)))
            diff=(g-p)[idx].mean(1);rat=py[idx].mean(1)/gy[idx].mean(1)
            target=targets[setting]['target']
            pairs.append({'setting':setting,'n_complete_three_arm_pairs':len(seeds),'seeds':seeds,'metric':metric,
                'outcome_difference_gosc_minus_periodic':[float((g-p).mean()),*map(float,np.percentile(diff,[2.5,97.5]))],
                'uplink_ratio_periodic_over_gosc':[float(py.mean()/gy.mean()),*map(float,np.percentile(rat,[2.5,97.5]))],
                'frozen_author_target':target,'gosc_mean_meets_frozen_target':bool(g.mean()<=target if task=='search' else g.mean()>=target),
                'periodic_mean_meets_frozen_target':bool(p.mean()<=target if task=='search' else p.mean()>=target),
                'inference_scope':'Exploratory N=10 workflow pilot; not a confirmatory method-benefit claim'})
    all_keys={j['job_id'] for j in jobs};got={r['job_id'] for r in records}
    complete=all_keys==got and len(records)==60 and len(done)==60 and len(pairs)==2 and all(p['n_complete_three_arm_pairs']==10 for p in pairs)
    statuses={s:sum(r['execution_status']==s for r in records) for s in ['completed','failed','timeout','interrupted']}
    cpu=sum(r['output']['worker_resources']['cpu_user_seconds']+r['output']['worker_resources']['cpu_system_seconds'] for r in done)
    rss=max((r['output']['worker_resources']['max_rss_kib'] for r in done),default=0)
    costs={'campaign_wall_seconds':run['elapsed_seconds'],'worker_cpu_seconds_completed_processes':cpu,
           'max_single_worker_rss_kib':rss,'max_active_workers':run['max_active_workers'],
           'worker_process_elapsed_seconds':{'mean':float(np.mean([r['process_elapsed_seconds'] for r in done])) if done else None,
             'median':float(np.median([r['process_elapsed_seconds'] for r in done])) if done else None,
             'p95':float(np.percentile([r['process_elapsed_seconds'] for r in done],95)) if done else None},
           'same_mix_1200_missions_wall_seconds_conditional':run['elapsed_seconds']*20 if complete else None,
           'projection_limit':'Only the two measured W100 scenes and these three arms; does not price unmeasured K10/clustered/W50/SNR-5, candidate searches or LLMs.',
           'gpu_workload':False,'peak_gpu_memory':None}
    value={'pilot_status':'complete' if complete else 'partial_or_failed','planned_missions':60,'terminal_records':len(records),
           'execution_counts':statuses,'all_keys_accounted':all_keys==got,'max_active_workers':run['max_active_workers'],
           'groups':groups,'paired_comparisons':pairs,'costs':costs,'stop_reason':run['stop_reason'],
           'full_campaign_status':'not_started','training_status':'not_started'}
    write_json(out/'pilot_summary.json',value)
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['job_id','setting','seed','scheme','execution_status','process_elapsed_seconds','completion_time','completed','found','saved_fraction','false_declarations','bits','symbols','dl_symbols']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in records:
            result=r.get('output',{}).get('result',{})
            w.writerow({k:r.get(k,result.get(k,'')) for k in fields})
    print(json.dumps(value),flush=True)
    return complete


def confirm_unstarted(previous, plan):
    """Allow explicit recovery only when the prior failed attempt launched no workers."""
    status=json.loads((previous/'status.json').read_text())
    manifest=json.loads((previous/'manifest.json').read_text())
    if status['status']!='failed' or manifest['stage']!='R4-A0' or manifest['git_commit']!=plan['head']:
        raise RuntimeError('Previous attempt is not a failed matching pilot')
    if manifest.get('config_sha256')!=hashlib.sha256(PLAN.read_bytes()).hexdigest() or set(manifest['seeds'])!=set(plan['pilot']['seeds']):
        raise RuntimeError('Previous attempt has a different plan/seed set')
    if any((previous/'outputs'/name).exists() for name in ['episodes.jsonl','events.jsonl','mission_status.json','execution_context.json']):
        raise RuntimeError('Prior attempt may have started work; automatic rerun forbidden')
    if (ROOT/'.local/r4-worker-tmp'/previous.name).exists():
        raise RuntimeError('Prior worker temporary area exists; inspect before retry')
    if "ModuleNotFoundError: No module named 'gosc'" not in (previous/'stderr.log').read_text():
        raise RuntimeError('No verified pre-mission import failure evidence')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('validate')
    p=sub.add_parser('execute');p.add_argument('--previous-unstarted-attempt')
    p=sub.add_parser('_worker');p.add_argument('--job',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require_hpc()
    if args.action=='_worker':worker(args.job,args.output);return 0
    if args.action=='validate':
        jobs=expand_plan(json.loads(PLAN.read_text()))
        print(json.dumps({'planned_missions':len(jobs),'scientific_missions_started':0}));return 0
    out=Path(os.environ['GOSC_OUTPUT_DIR']);run_dir=Path(os.environ['GOSC_RUN_DIR'])
    assert out.resolve()==(run_dir/'outputs').resolve() and run_dir.parent==ROOT/'research/sync/runs'
    before=snapshot();plan=json.loads(PLAN.read_text());jobs=expand_plan(plan)
    write_json(out/'plan_snapshot.json',plan);write_json(out/'jobs.json',jobs)
    python=copy_environment(out)
    source=json.loads((ROOT/'.local/hpc-sync/latest_manifest.json').read_text())
    if source['head']!=plan['head']:raise RuntimeError('Plan HEAD mismatch')
    for e in source['files']:
        if hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()!=e['remote_sha256']:
            raise RuntimeError('Source changed since verified sync: '+e['path'])
    for p in (ROOT/'research/sync/runs').glob('*/manifest.json'):
        if p.parent==run_dir:continue
        v=json.loads(p.read_text())
        if v['kind']=='simulation' and set(v.get('seeds',[])) & set(plan['pilot']['seeds']):
            if p.parent.name != args.previous_unstarted_attempt:
                raise RuntimeError('Pilot seeds already registered: '+p.parent.name)
            confirm_unstarted(p.parent, plan)
    stop={'requested':False}
    def interrupted(signum,frame):stop['requested']=True
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,interrupted)
    start=time.monotonic()
    write_json(out/'execution_context.json',{'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'runtime':str(python),'worker_thread_limit':1,'workers':2,'per_episode_timeout_seconds':120,
        'campaign_budget_seconds':1200,'baseline_head':source['head'],'source_sync_id':source['sync_id'],
        'seed_policy':'9000-9009 workflow pilot; no parameter selection or training',
        'previous_unstarted_attempt':args.previous_unstarted_attempt,
        'cost_accounting':'Base run_episode symbols and dl_symbols; not full realistic UL+DL control accounting'})
    try:
        result=run_jobs(jobs,out,ROOT/'.local/r4-worker-tmp'/run_dir.name,
            lambda job,spec,dest:[python,Path(__file__).resolve(),'_worker','--job',spec,'--output',dest],
            validate_payload,2,120,max(0.0,1200-(time.monotonic()-start)),cancel=lambda:stop['requested'])
        targets=json.loads((ROOT/'results/rev_validation.json').read_text())
        complete=summarize(result,jobs,out,targets)
    finally:
        after=snapshot();write_json(out/'input_integrity.json',{'before':before,'after':after,'unchanged':before==after})
        if before!=after:raise RuntimeError('Protected inputs changed')
    return 0 if complete else 1


if __name__=='__main__':
    raise SystemExit(main())
