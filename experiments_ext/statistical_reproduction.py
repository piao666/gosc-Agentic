"""Approved R4-S1 runner: retains exact discrepancies; never rewrites strict R4."""
import argparse
from dataclasses import asdict
import datetime as dt
import importlib.metadata as md
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import time
import traceback

for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name]='1'
os.environ.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg')

from experiments_ext.reproduce import ROOT, BASE, save, sha, git, check_protected
from experiments_ext.campaign import r4_jobs, _job, config_key

OLD = ROOT/'.local/reproduction/2026-10-15-baseline-v1'
PROTOCOL = ROOT/'research/reproduction/statistical_protocol_v1.md'


def prepare(run):
    from gosc import Config
    if json.loads((OLD/'r3_manifest.json').read_text())['status'] != 'passed':
        raise RuntimeError('R3 prerequisite not passed')
    check_protected(OLD)
    lock={}
    for line in (ROOT/'requirements-windows.lock.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version=line.split('==');lock[name]=md.version(name)
            if lock[name]!=version:raise RuntimeError('Frozen dependency differs: '+name)
    jobs, selections=r4_jobs(OLD)
    run.mkdir(parents=True,exist_ok=False)
    configs={config_key(j['cfg']):asdict(j['cfg']) for j in jobs}
    save(run/'configs.json',configs)
    serialized=[dict(job_id=i,config_key=config_key(j['cfg']),
        **{k:v for k,v in j.items() if k!='cfg'}) for i,j in enumerate(jobs)]
    save(run/'jobs.json',serialized)
    snapshot=run/'source';snapshot.mkdir()
    paths=[Path(__file__),ROOT/'experiments_ext/statistical_agreement.py',ROOT/'experiments_ext/analyze_statistical_reproduction.py',ROOT/'experiments_ext/campaign.py',
           ROOT/'experiments_ext/reproduce.py',ROOT/'experiments_ext/summarize.py',ROOT/'extensions/receiver_oracle.py',PROTOCOL]
    for p in paths:
        with (snapshot/p.name).open('xb') as f:f.write(p.read_bytes())
    save(run/'plan.json',dict(experiment_id=run.name,status='prepared',
        date=dt.datetime.now(dt.timezone.utc).isoformat(),git_commit=git('rev-parse','HEAD'),
        baseline_commit=BASE,working_tree_dirty=bool(git('status','--short')),
        python=sys.version,os=platform.platform(),dependencies=lock,
        dependencies_lock_sha256=sha(ROOT/'requirements-windows.lock.txt'),
        hardware_manifest='research/logs/environment-2026-10-12/hardware.json',
        protocol_sha256=sha(PROTOCOL),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        config_sha256=sha(run/'configs.json'),jobs_sha256=sha(run/'jobs.json'),
        jobs=5200,workers_max=4,timeout_seconds=2700,selections=selections,
        source_prior_exposure='1399 strict-stage retained results and seed-0 probes already observed',
        llm_cache_mode='not_used',agent_models=['Planner'],
        split='0-99 original evaluation; 3000-3099 frozen validation; no calibration tuning',
        gate=dict(metric_count=104,bootstrap_resamples=20000,statistical_seed=20261015,
            search_relative_margin=.05,resource_relative_margin=.05,rescue_absolute_margin=.02),
        previous_strict_stage='failed_preserved',protected_inputs=check_protected(OLD)))
    print('Prepared',run,'5200 new executions',flush=True)


def verify_plan(run):
    p=json.loads((run/'plan.json').read_text())
    for key,name in [('config_sha256','configs.json'),('jobs_sha256','jobs.json')]:
        if sha(run/name)!=p[key]:raise RuntimeError('Frozen plan modified')
    for rel,expected in p['source_sha256'].items():
        if sha(ROOT/rel)!=expected:raise RuntimeError('Execution source/protocol changed: '+rel)
    check_protected(OLD)
    return p


def load_jobs(run):
    from gosc import Config
    configs=json.loads((run/'configs.json').read_text())
    records=json.loads((run/'jobs.json').read_text())
    for j in records:
        cfg=dict(configs[j['config_key']]);cfg['rates']=tuple(cfg['rates']);cfg['llm_agents']=tuple(cfg['llm_agents'])
        j['cfg']=Config(**cfg)
    return records


def execute(run,workers):
    plan=verify_plan(run);jobs=load_jobs(run)
    out=run/'r4-statistical';out.mkdir(exist_ok=False)
    started=dt.datetime.now(dt.timezone.utc).isoformat();t=time.perf_counter()
    count=0;mismatches=0
    try:
        with (out/'raw.jsonl').open('x',encoding='utf-8') as f,mp.Pool(workers) as pool:
            iterator=pool.imap_unordered(_job,jobs,chunksize=1)
            while count<len(jobs):
                if time.perf_counter()-t>plan['timeout_seconds']:raise TimeoutError('Approved R4 time budget exceeded')
                try:row=iterator.next(timeout=30)
                except mp.TimeoutError:
                    print('R4-S1 heartbeat',count,'elapsed',round(time.perf_counter()-t),flush=True);continue
                f.write(json.dumps(row,allow_nan=False)+'\n');count+=1
                mismatches+=bool(row.get('reference_differences'))
                if row['status']!='completed':raise RuntimeError('Mission failed; raw evidence retained')
                cfg=jobs[row['job_id']]['cfg'];o=row['output']
                if not 0<=o['symbols']<=cfg.n_agents*cfg.max_steps*cfg.symbols_per_slot:
                    raise RuntimeError('Invalid mission channel-use bound')
                if count%100==0 or count==len(jobs):
                    f.flush();print(f'R4-S1 {count}/{len(jobs)} elapsed={time.perf_counter()-t:.1f}s exact-discrepancies={mismatches}',flush=True)
    except Exception:
        save(out/'failure.json',dict(status='failed',completed=count,traceback=traceback.format_exc(),
            exact_reference_mismatch_records=mismatches,elapsed_seconds=time.perf_counter()-t));raise
    save(out/'execution_manifest.json',dict(status='completed_pending_statistical_gate',completed=count,
        fresh_executions=count,reused_previous_runs=0,exact_reference_mismatch_records=mismatches,
        start_utc=started,elapsed_seconds=time.perf_counter()-t,workers=workers,
        raw_sha256=sha(out/'raw.jsonl'),plan_sha256=sha(run/'plan.json'),protected_inputs=check_protected(OLD)))


def analyze(run):
    from experiments_ext.analyze_statistical_reproduction import analyze as analyze_impl
    analyze_impl(run)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=['prepare','run','analyze'])
    ap.add_argument('--run-id',required=True);ap.add_argument('--workers',type=int,choices=range(1,5),default=4)
    args=ap.parse_args()
    if Path(args.run_id).name!=args.run_id or args.run_id in ('.','..'):ap.error('Invalid run-id')
    run=ROOT/'.local/reproduction'/args.run_id
    if args.stage=='prepare':prepare(run)
    elif args.stage=='run':execute(run,args.workers)
    else:analyze(run)


if __name__=='__main__':
    mp.freeze_support();main()
