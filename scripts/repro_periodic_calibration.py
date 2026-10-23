"""HPC-only prospective GP-v1 preparation, cost probe, calibration and power plan.

No test execution entry point. Inputs/outputs are immutable run artifacts.
"""
import argparse
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import signal
from statistics import NormalDist
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gosc.config import Config
from extensions.paid_receiver_service import ServiceConfig
from extensions.paired_paid_simulation import PairedPaidSimulation


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')


def catalog(p):
    cases=[dict(id='bits',mode='bits',price=0.,eps=.02,interval=1,pose=False),
           dict(id='aoi',mode='aoi',price=0.,eps=.02,interval=1,pose=False)]
    for k in p['periodic_intervals']:
        for eps in p['periodic_filter_eps']:
            cases.append(dict(id=f'periodic_k{k}_eps{eps}',mode='periodic',price=0.,eps=eps,interval=k,pose=False))
    cases.extend([dict(id='public_tom',mode='tom',price=1e-5,eps=.02,interval=1,pose=False),
                  dict(id='paid_pose',mode='tom',price=1e-5,eps=.02,interval=1,pose=True)])
    return cases


def make(p,case,seed,steps):
    cfg=Config(max_steps=steps,energy_price=case['price'],filter_eps=case['eps'],sem_interval=case['interval'])
    return PairedPaidSimulation(cfg,seed,ServiceConfig(**p['service']),case['mode'],case['pose'],p['dl_loss'])


def prepare(p,out,config):
    # Registered manifests and original pool argument catalogs are the seed
    # authority; hashes logged by previous prospective pilots supplement them.
    integers=set();known_worlds=set();sources=[]
    def walk(x,key=''):
        if isinstance(x,bool):return
        if isinstance(x,int):integers.add(x)
        elif isinstance(x,list):
            for y in x:walk(y,key)
        elif isinstance(x,dict):
            for k,v in x.items():walk(v,k)
        elif isinstance(x,str) and ('sha256' in key or 'fingerprint' in key) and len(x)==64:
            known_worlds.add(x)
    candidates=set((ROOT/'research/sync/runs').glob('*/manifest.json'))
    candidates.update((ROOT/'research/protocols').glob('*.json'))
    for name in ('pool-plans.jsonl','selection_episodes.jsonl','protocol.json','calibration.jsonl','validation.jsonl','results.jsonl'):
        candidates.update((ROOT/'research/sync/runs').glob('*/outputs/'+name))
    for path in sorted(candidates):
        if path==config or 'hpc-periodic-' in path.as_posix():continue
        if path.suffix=='.jsonl':
            with path.open() as f:
                for line in f:
                    if line.strip():walk(json.loads(line))
        else:walk(read(path))
        sources.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path),'bytes':path.stat().st_size})
    all_seeds=p['probe_seeds']+p['calibration_seeds']+list(range(p['test_reserved_seeds'][0],p['test_reserved_seeds'][1]+1))
    if len(all_seeds)!=len(set(all_seeds)):raise RuntimeError('New split overlap')
    conflicts=sorted(set(all_seeds)&integers)
    if conflicts:raise RuntimeError('Registered seed/integer collision: '+repr(conflicts))
    if min(all_seeds)<=17000000:raise RuntimeError('Historical domain excluded')
    worlds={};case=catalog(p)[0]
    for seed in all_seeds:
        s=make(p,case,seed,400);fp=s.input_world_sha256
        if fp in known_worlds or fp in worlds.values():raise RuntimeError('World collision')
        worlds[str(seed)]=fp
    source_paths=[*sorted((ROOT/'gosc').glob('*.py')),*sorted((ROOT/'extensions').glob('*.py')),
                  Path(__file__),config]
    frozen={'status':'frozen_before_new_mission_outcomes','plan':p,'plan_sha256':digest(config),
            'cases':catalog(p),'worlds':worlds,'source_sha256':{str(x.relative_to(ROOT)):digest(x) for x in source_paths},
            'registry':sources,'registered_integer_count':len(integers),'known_hash_count':len(known_worlds),
            'scope':'All run manifests, top-level protocol JSON, registered pool-plan/selection/pilot result catalogs. Unregistered external runs and unlogged historical world hashes cannot be excluded.',
            'seed_conflicts':conflicts,'test_simulations_run':0}
    save(out/'frozen.json',frozen)
    print(json.dumps({'cases':len(frozen['cases']),'worlds':len(worlds),'catalogs':len(sources),'seed_conflicts':conflicts}))


def check_sources(frozen):
    for name,expected in frozen['source_sha256'].items():
        if digest(ROOT/name)!=expected:raise RuntimeError('Source changed after freeze: '+name)


def missions(frozen,out,phase,steps,seeds):
    check_sources(frozen);p=frozen['plan'];rows=[]
    for seed in seeds:
        for case in frozen['cases']:
            start=time.monotonic();cpu=time.process_time()
            def expired(*_):raise TimeoutError('Per-mission 60 seconds')
            signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,60)
            try:
                s=make(p,case,seed,steps)
                if s.input_world_sha256!=frozen['worlds'][str(seed)]:raise RuntimeError('World changed')
                result=s.run();cost=result['service']['cost']
                assert cost['ul_uses']==sum(e['ul_uses'] for e in s.service.events if e['kind']=='ul')
                assert cost['dl_uses']==sum(e['uses'] for e in s.service.events if e['kind']=='dl')
                row={'status':'completed','phase':phase,'seed':seed,'case_id':case['id'],'case':case,
                     'result':result,'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time()-cpu,
                     'received_task_items':len(s._local_seen),'edge_task_items':len(s._edge_seen),
                     'final_cache_sizes':{str(k):len(v) for k,v in s.service.knowledge.cache.items()}}
                # Preserve original raw per-mission result, including curve and censored queues.
                save(out/(str(seed)+'-'+case['id']+'.json'),row);rows.append(row)
                print(json.dumps({'seed':seed,'case':case['id'],'seconds':row['wall_seconds']}),flush=True)
            except Exception as e:
                save(out/(str(seed)+'-'+case['id']+'-failure.json'),{'status':'failed','error':repr(e),'seed':seed,'case':case})
                raise
            finally:signal.setitimer(signal.ITIMER_REAL,0)
    save(out/'results.json',rows)
    return rows


def probe(frozen,out):
    p=frozen['plan'];rows=missions(frozen,out,'cost_probe',p['probe_steps'],p['probe_seeds'])
    by={c['id']:max(r['wall_seconds'] for r in rows if r['case_id']==c['id']) for c in frozen['cases']}
    estimate=2*sum(by.values())/p['probe_steps']*p['calibration_steps']*len(p['calibration_seeds'])
    budget={'status':'calibration_budget_passed' if estimate<=p['calibration_projection_gate_seconds'] else 'calibration_budget_blocked',
            'case_max_seconds':by,'projected_calibration_seconds_with_2x_margin':estimate,
            'projection_limit_seconds':p['calibration_projection_gate_seconds'],
            'hard_timeout_seconds':p['calibration_timeout_seconds'],
            'caveat':'24-slot linear extrapolation can underestimate growing queues; hard timeout remains binding',
            'effect_statistics_computed':False}
    save(out/'budget.json',budget);print(json.dumps(budget))


def analyse(frozen,rows,out):
    p=frozen['plan'];ids=[c['id'] for c in frozen['cases']];seeds=p['calibration_seeds']
    def series(case,field):
        chosen=sorted((r for r in rows if r['case_id']==case),key=lambda r:r['seed'])
        if [r['seed'] for r in chosen]!=seeds:raise RuntimeError('Incomplete paired data')
        if field=='cost':return np.array([r['result']['service']['cost']['ul_uses']+r['result']['service']['cost']['dl_uses'] for r in chosen],float)
        return np.array([r['result'][field] for r in chosen],float)
    summary=[]
    for case in ids:
        rr=[r for r in rows if r['case_id']==case]
        summary.append({'id':case,'N':len(rr),'mean_T':float(series(case,'completion_time').mean()),
                        'mean_total_UL_DL':float(series(case,'cost').mean()),
                        'completed':int(series(case,'completed').sum()),
                        'mean_found':float(series(case,'found').mean()),
                        'mean_CPU_service_seconds':float(np.mean([r['result']['service']['cost']['cpu_seconds'] for r in rr])),
                        'mean_wall_seconds':float(np.mean([r['wall_seconds'] for r in rr]))})
    simple=[r for r in summary if r['id'] not in ('public_tom','paid_pose')]
    best=min(simple,key=lambda r:(r['mean_T'],r['mean_total_UL_DL'],r['id']))['id']
    rng=np.random.default_rng(p['analysis_seed']);n=len(seeds)
    idx=rng.integers(0,n,(p['bootstrap_resamples'],n));q=NormalDist()
    z=q.inv_cdf(1-p['alpha']/p['bonferroni_family'])+q.inv_cdf(p['endpoint_power_target'])
    comparisons=[];required=[];negative=False;degenerate=False
    for case in (best,'public_tom'):
        gain=series(case,'completion_time')-series('paid_pose','completion_time')
        a=series('paid_pose','cost');b=series(case,'cost')
        if b.mean()<=0:raise RuntimeError('Zero baseline cost')
        ratio=float(a.mean()/b.mean());influence=(a-ratio*b)/b.mean()
        if ratio<=0:raise RuntimeError('Nonpositive cost ratio')
        cost_log=influence/ratio
        sd_gain=max(float(gain.std(ddof=1)),float(np.quantile(gain[idx].std(axis=1,ddof=1),.95)))
        sd_cost=max(float(cost_log.std(ddof=1)),float(np.quantile(cost_log[idx].std(axis=1,ddof=1),.95)))
        degenerate|=(sd_gain==0 or sd_cost==0)
        ng=math.ceil((z*sd_gain/(p['design_alternative_task_gain_slots']-p['minimum_task_gain_slots']))**2)
        nc=math.ceil((z*sd_cost/math.log(p['maximum_mean_cost_ratio']/p['design_alternative_cost_ratio']))**2)
        required.extend([ng,nc]);negative|=(gain.mean()<=0 and ratio>p['maximum_mean_cost_ratio'])
        boot_ratio=a[idx].mean(axis=1)/b[idx].mean(axis=1)
        comparisons.append({'comparator':case,'N':n,'mean_gain_slots':float(gain.mean()),
          'exploratory_gain_95CI':np.quantile(gain[idx].mean(axis=1),[.025,.975]).tolist(),
          'mean_cost_ratio':ratio,'exploratory_ratio_95CI':np.quantile(boot_ratio,[.025,.975]).tolist(),
          'gain_SD_planning_upper':sd_gain,'log_ratio_influence_SD_planning_upper':sd_cost,
          'N_task':ng,'N_cost':nc})
    candidate_n=max([p['test_N_min'],*required]);wall=max(r['wall_seconds'] for r in rows)*2*candidate_n*3
    reasons=[]
    if negative:reasons.append('Calibration has nonpositive task gain and >1.05 cost for a primary comparison')
    if degenerate:reasons.append('Zero observed variance cannot establish stable planning variance')
    if candidate_n>p['test_N_max']:reasons.append('Required planning N exceeds prespecified 200-world feasibility cap')
    decision={'status':'No-Go' if reasons else 'frozen_proposal_pending_test_authorization',
              'selected_M0star':best,'calibration_N':n,'candidate_test_N':candidate_n,
              'N_cap':p['test_N_max'],'executable_test_N':None if reasons else candidate_n,
              'proposed_test_missions':None if reasons else 3*candidate_n,
              'proposed_test_wall_seconds_2x_worst_calibration':None if reasons else math.ceil(wall),
              'test_seeds':[] if reasons else list(range(p['test_reserved_seeds'][0],p['test_reserved_seeds'][0]+candidate_n)),
              'test_run':False,'reasons':reasons,'comparisons':comparisons,'all_candidates':summary,
              'limitations':'Exploratory 12-world calibration, one W/price/CPU/DL setting and finite periodic grid; normal/bootstrap planning approximation, not guaranteed power, not matched multi-point frontier or confirmatory superiority. Zero-variance and N-cap gates enforced.',
              'training':'No-Go','paid_effect_confirmed':False}
    save(out/'decision.json',decision);print(json.dumps(decision))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode',choices=['prepare','probe','calibrate'],required=True)
    ap.add_argument('--config',type=Path,default=ROOT/'research/protocols/periodic_crn_stage_v1.json')
    ap.add_argument('--frozen',type=Path);ap.add_argument('--budget',type=Path);a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    out=Path(os.environ['GOSC_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
    if a.mode=='prepare':prepare(read(a.config),out,a.config.resolve());return
    frozen=read(a.frozen)
    if a.mode=='probe':probe(frozen,out);return
    budget=read(a.budget)
    if budget['status']!='calibration_budget_passed':raise RuntimeError('Cost gate blocks calibration')
    rows=missions(frozen,out,'independent_calibration',frozen['plan']['calibration_steps'],frozen['plan']['calibration_seeds'])
    analyse(frozen,rows,out)


if __name__=='__main__':main()
