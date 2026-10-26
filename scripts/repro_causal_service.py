"""HPC-only GP-v2 freeze, bounded probe and conditional calibration. No test mode."""
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
from extensions.causal_paid_service import CausalPolicy
from extensions.causal_paid_simulation import CausalPaidSimulation

def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def cases(p):
    rows=[dict(id=m,mode=m,arm='public',price=0.,eps=.02,k=1) for m in ('bits','aoi')]
    rows += [dict(id=f'periodic_k{k}_eps{eps}',mode='periodic',arm='public',price=0.,eps=eps,k=k)
             for k in p['periodic_intervals'] for eps in p['periodic_filter_eps']]
    rows += [dict(id=f'{arm}_p{price:g}',mode='tom',arm=arm,price=price,eps=.02,k=1)
             for arm in ('public','pose','age') for price in p['prices']]
    rows += [dict(id=arm+'_p1e-05',mode='tom',arm=arm,price=1e-5,eps=.02,k=1) for arm in ('ignore','shuffle')]
    assert len(rows)==p['candidate_count'] and len({r['id'] for r in rows})==len(rows)
    return rows

def make(p,c,seed,steps):
    cfg=Config(max_steps=steps,energy_price=c['price'],filter_eps=c['eps'],sem_interval=c['k'])
    return CausalPaidSimulation(cfg,seed,ServiceConfig(**p['service']),c['mode'],c['arm'],CausalPolicy(**p['policy']),p['dl_loss'])

def prepare(p,out,config):
    integers=set();hashes=set();catalog=[]
    def walk(x,key=''):
        if isinstance(x,bool):return
        if isinstance(x,int):integers.add(x)
        elif isinstance(x,list):
            for v in x:walk(v,key)
        elif isinstance(x,dict):
            for k,v in x.items():walk(v,k)
        elif isinstance(x,str) and len(x)==64 and ('sha256' in key or 'fingerprint' in key or key.isdigit()):hashes.add(x)
    paths=set((ROOT/'research/sync/runs').glob('*/manifest.json'))
    paths.update((ROOT/'research/protocols').glob('*.json'))
    for name in ('frozen.json','results.json','pool-plans.jsonl','selection_episodes.jsonl','protocol.json','calibration.jsonl','validation.jsonl','results.jsonl'):
        paths.update((ROOT/'research/sync/runs').glob('*/outputs/'+name))
    for path in sorted(paths):
        if path.resolve()==config.resolve():continue
        if path.suffix=='.jsonl':
            with path.open() as f:
                for line in f:
                    if line.strip():walk(json.loads(line))
        else:walk(read(path))
        catalog.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path)))
    seeds=p['probe_seeds']+p['calibration_seeds']+list(range(p['test_reserved_seeds'][0],p['test_reserved_seeds'][1]+1))
    if len(set(seeds))!=len(seeds) or set(seeds)&integers:raise RuntimeError('Registered seed/integer collision')
    worlds={}
    for seed in seeds:
        fp=make(p,cases(p)[0],seed,400).input_world_sha256
        if fp in hashes or fp in worlds.values():raise RuntimeError('World collision')
        worlds[str(seed)]=fp
    sources=[*sorted((ROOT/'gosc').glob('*.py')),*sorted((ROOT/'extensions').glob('*.py')),Path(__file__),config]
    save(out/'frozen.json',dict(status='frozen_before_new_mission_outcomes',plan=p,cases=cases(p),worlds=worlds,
         source_sha256={x.relative_to(ROOT).as_posix():digest(x) for x in sources},registry=catalog,
         registered_integer_count=len(integers),known_hash_count=len(hashes),seed_conflicts=[],test_simulations_run=0,
         scope='Discoverable registered manifests/protocols and named output catalogs; unregistered or unlogged history cannot be excluded'))
    print(json.dumps(dict(worlds=len(worlds),cases=len(cases(p)),catalogs=len(catalog),collisions=0)))

def check_sources(f):
    for name,sha in f['source_sha256'].items():
        if digest(ROOT/name)!=sha:raise RuntimeError('Source changed after freeze: '+name)

def missions(f,out,phase):
    check_sources(f);p=f['plan'];steps=p['probe_steps'] if phase=='probe' else p['calibration_steps']
    seeds=p['probe_seeds'] if phase=='probe' else p['calibration_seeds'];rows=[]
    for seed in seeds:
        for c in f['cases']:
            wall=time.monotonic();cpu=time.process_time()
            def expired(*_):raise TimeoutError('Per-mission hard timeout')
            signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,p['per_mission_timeout_seconds'])
            try:
                s=make(p,c,seed,steps);assert s.input_world_sha256==f['worlds'][str(seed)]
                result=s.run();cost=result['service']['cost']
                assert cost['ul_uses']==sum(e['ul_uses'] for e in s.service.events if e['kind']=='ul')
                assert cost['dl_uses']==sum(e['uses'] for e in s.service.events if e['kind']=='dl')
                assert cost['valuation_cpu_seconds']==p['policy']['valuation_seconds']*result['selection_calls'] or math.isclose(cost['valuation_cpu_seconds'],p['policy']['valuation_seconds']*result['selection_calls'])
                row=dict(seed=seed,case_id=c['id'],case=c,phase=phase,status='completed',result=result,
                         wall_seconds=time.monotonic()-wall,cpu_seconds=time.process_time()-cpu,
                         distinct_local_task_receipts=len(s._local_seen),edge_tasks=len(s._edge_seen),
                         recipient_coverage=float(len(s._local_seen)/(max(1,len(s._edge_seen))*s.cfg.n_agents)))
                save(out/f'{seed}-{c["id"]}.json',row)
                # Raw actual service events and clocks are evidence, never controller inputs.
                with (out/f'{seed}-{c["id"]}-events.jsonl').open('x') as log:
                    for kind,data in [('resource',s.service.events),('task_attempt',s.service.attempt_log),('replay_offer',s.service.replay_log),('cpu',s.service.cpu_log)]:
                        for event in data:log.write(json.dumps(dict(stream=kind,**event))+'\n')
                rows.append(row);print(json.dumps(dict(seed=seed,case=c['id'],wall=row['wall_seconds'])),flush=True)
            except Exception as exc:
                save(out/f'{seed}-{c["id"]}-failure.json',dict(status='failed',seed=seed,case=c,error=repr(exc)));raise
            finally:signal.setitimer(signal.ITIMER_REAL,0)
    save(out/'results.json',rows);return rows

def cost(r,key):
    c=r['result']['service']['cost']
    return c['ul_uses']+c['dl_uses'] if key=='comm' else c['cpu_seconds']

def analyse(f,rows,out):
    p=f['plan'];n=len(p['calibration_seeds']);summary=[]
    def vec(case,key):
        rr=sorted((r for r in rows if r['case_id']==case),key=lambda r:r['seed'])
        assert [r['seed'] for r in rr]==p['calibration_seeds']
        return np.array([cost(r,key) if key in ('comm','cpu') else r['result'][key] for r in rr],float)
    for c in f['cases']:
        rr=[r for r in rows if r['case_id']==c['id']]
        summary.append(dict(id=c['id'],mode=c['mode'],arm=c['arm'],price=c['price'],N=n,
          mean_T=float(vec(c['id'],'completion_time').mean()),mean_comm=float(vec(c['id'],'comm').mean()),
          mean_cpu=float(vec(c['id'],'cpu').mean()),completed=int(vec(c['id'],'completed').sum()),
          mean_coverage=float(np.mean([r['recipient_coverage'] for r in rr])),
          mean_mission_process_seconds=float(np.mean([r['cpu_seconds'] for r in rr])),
          mean_selection_process_seconds=float(np.mean([r['result']['selection_process_seconds'] for r in rr]))))
    def best(group):return min(group,key=lambda r:(r['mean_T'],r['mean_comm'],r['id']))
    simple=best([r for r in summary if r['mode']!='tom']);public=best([r for r in summary if r['mode']=='tom' and r['arm']=='public'])
    pose=best([r for r in summary if r['arm']=='pose']);rng=np.random.default_rng(p['analysis_seed'])
    idx=rng.integers(0,n,(p['bootstrap_resamples'],n));comparisons=[];required=[];reasons=[]
    z=NormalDist().inv_cdf(1-p['alpha']/p['bonferroni_family'])+NormalDist().inv_cdf(p['endpoint_power_target'])
    for baseline in (simple,public):
        a=pose['id'];b=baseline['id'];gain=vec(b,'completion_time')-vec(a,'completion_time')
        sd=max(float(gain.std(ddof=1)),float(np.quantile(gain[idx].std(axis=1,ddof=1),.95)))
        ng=math.ceil((z*sd/(p['design_alternative_task_gain_slots']-p['minimum_task_gain_slots']))**2);required.append(ng)
        entry=dict(comparator=b,pose=a,N=n,mean_gain_slots=float(gain.mean()),gain_95CI=np.quantile(gain[idx].mean(axis=1),[.025,.975]).tolist(),N_task=ng)
        if not sd:reasons.append('Degenerate task variance: '+b)
        for key in ('comm','cpu'):
            av=vec(a,key);bv=vec(b,key);ratio=float(av.mean()/bv.mean())
            influence=(av-ratio*bv)/bv.mean()/ratio
            sd=max(float(influence.std(ddof=1)),float(np.quantile(influence[idx].std(axis=1,ddof=1),.95)))
            needed=math.ceil((z*sd/math.log(p['maximum_mean_cost_ratio']/p['design_alternative_cost_ratio']))**2);required.append(needed)
            entry[key+'_ratio']=ratio;entry[key+'_ratio_95CI']=np.quantile(av[idx].mean(axis=1)/bv[idx].mean(axis=1),[.025,.975]).tolist();entry['N_'+key]=needed
            if not sd:reasons.append('Degenerate resource variance: '+b+'/'+key)
            if not .95<=ratio<=1.05:reasons.append('Selected primary points lack joint matched resource support: '+b+'/'+key)
            if gain.mean()<=0 and ratio>1.05:reasons.append('Nonpositive task gain with increased cost: '+b+'/'+key)
        comparisons.append(entry)
    candidate=max(p['test_N_min'],*required)
    if candidate>p['test_N_max']:reasons.append('Planning N exceeds prespecified 200-world cap')
    frontier=[]
    for arm in ('public','pose','age'):
        group=[r for r in summary if r['mode']=='tom' and r['arm']==arm]
        for point in group:
            dominated=any(q['id']!=point['id'] and all(q[k]<=point[k] for k in ('mean_T','mean_comm','mean_cpu')) and any(q[k]<point[k] for k in ('mean_T','mean_comm','mean_cpu')) for q in group)
            frontier.append(dict(**point,dominated=dominated))
    supported=[dict(pose=a['id'],baseline=b['id'],comm_ratio=a['mean_comm']/b['mean_comm'],cpu_ratio=a['mean_cpu']/b['mean_cpu'])
               for a in summary if a['arm']=='pose' for b in summary if b['arm']=='public'
               if .95<=a['mean_comm']/b['mean_comm']<=1.05 and .95<=a['mean_cpu']/b['mean_cpu']<=1.05]
    decision=dict(status='No-Go' if reasons else 'proposal_pending_formal_test_authorization',calibration_N=n,
          selected_M0star=simple['id'],selected_public=public['id'],selected_pose=pose['id'],comparisons=comparisons,
          all_candidates=summary,discrete_frontier=frontier,joint_cost_supported_pairs=supported,
          candidate_test_N=candidate,executable_test_N=None if reasons else candidate,
          proposed_test_wall_seconds=None if reasons else math.ceil(2*max(r['wall_seconds'] for r in rows)*3*candidate),
          confirmatory_test_run=False,test_missions_run=0,training='No-Go',paid_benefit_established=False,
          reasons=sorted(set(reasons)),scope=p['limitations'])
    save(out/'decision.json',decision);print(json.dumps(decision))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--mode',choices=['prepare','probe','calibrate'],required=True)
    ap.add_argument('--config',type=Path,default=ROOT/'research/protocols/causal_service_stage_v2.json');ap.add_argument('--frozen',type=Path);ap.add_argument('--budget',type=Path)
    a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    out=Path(os.environ['GOSC_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
    if a.mode=='prepare':prepare(read(a.config),out,a.config.resolve());return
    f=read(a.frozen);check_sources(f)
    if a.mode=='probe':
        rows=missions(f,out,'probe');p=f['plan']
        estimate=2*sum(max(r['wall_seconds'] for r in rows if r['case_id']==c['id']) for c in f['cases'])/p['probe_steps']*p['calibration_steps']*len(p['calibration_seeds'])
        budget=dict(status='passed' if estimate<=p['calibration_projection_gate_seconds'] else 'blocked',projection_seconds_2x=estimate,projection_limit=p['calibration_projection_gate_seconds'],hard_timeout=p['calibration_timeout_seconds'],caveat='Short-run extrapolation can underestimate growth; hard timeout binding')
        save(out/'budget.json',budget);print(json.dumps(budget));return
    if read(a.budget)['status']!='passed':raise RuntimeError('Probe budget blocks calibration')
    rows=missions(f,out,'calibration');analyse(f,rows,out)

if __name__=='__main__':main()
