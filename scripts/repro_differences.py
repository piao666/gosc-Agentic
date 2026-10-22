"""HPC-only coverage reanalysis and bounded diagnostic reruns of published cases."""
import argparse
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
from hpc_runs import ROOT,require_hpc,write_json
from repro_compare import compare_file,equal,load
sys.path.insert(0,str(ROOT))


def audit(out):
    reports=[]
    for stage in ['selection','selection-fresh','c-frontier','c-where']:
        folder=ROOT/f'research/sync/runs/ordered-{stage}-20261019/outputs/legacy_results'
        for p in folder.glob('*'):
            if p.suffix not in ['.json','.jsonl']:continue
            original=ROOT/'results'/p.name
            if not original.exists():original=original.with_name(original.name+'.gz')
            if original.exists():reports.append({'stage':stage}|compare_file(p,original))
    write_json(out/'coverage_comparison.json',{'files':reports,'original_outputs_modified':False})
    assert all(r['status']!='invalid_identity' for r in reports)
    catalog=json.loads((ROOT/'research/sync/runs/hpc-remaining-inventory-20261019/outputs/selection_catalog.json').read_text())
    cases=[{**c,'case':i} for i,c in enumerate(catalog)]
    selection=ROOT/'research/sync/runs/ordered-selection-20261019/outputs'
    mismatch=json.loads((selection/'selection_audit.json').read_text())['historical_mismatches']
    keys={(v['case'],v['seed']) for v in mismatch}
    selected={}
    with (selection/'selection_episodes.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line)
            if (row['case'],row['seed']) in keys or (row['case']==0 and row['seed']==0):selected[(row['case'],row['seed'])]=row
    details=[]
    for k in sorted(keys):
        case=cases[k[0]];old=next(r for r in case['original_seed_metrics'] if r['seed']==k[1]);actual=selected[k]
        details.append({'case':k[0],'seed':k[1],'scheme':case['scheme'],'point':case['point'],'setting':case['setting'],
            'metric':case['metric'],'outcome_actual':actual[case['metric']],'outcome_original':old['outcome'],
            'symbols_actual':actual['symbols'],'symbols_original':old['symbols'],
            'differs_with_tolerance':not equal(actual[case['metric']],old['outcome']) or not equal(actual['symbols'],old['symbols'])})
    write_json(out/'selection_difference_details.json',details)
    from experiments.run_revision import experiments
    from repro_selection import configuration
    native=experiments();probes=[]
    for stage,exp in [('c-frontier','frontier'),('c-where','where_tom')]:
        result=next(r for r in reports if r['stage']==stage)
        current=load(ROOT/f'research/sync/runs/ordered-{stage}-20261019/outputs/legacy_results'/result['file'])
        reference=load(ROOT/'results'/result['file'])
        for scheme in ['gosc_bits','gosc_aoi']:
            delta=next(d for d in result['mismatches'] if json.loads(d['key'])[0]==scheme)
            sch,param,seed=json.loads(delta['key'])
            cfg=next(cfg for s,p,cfg in native[exp] if s==sch and p==param)
            actual=next(r for r in current if (r['scheme'],r['param'],r['seed'])==(sch,param,seed))
            original=next(r for r in reference if (r['scheme'],r['param'],r['seed'])==(sch,param,seed))
            probes.append({'source':stage,'scheme':sch,'param':param,'seed':seed,'config':dataclasses.asdict(cfg),'actual':actual,'original':original})
    for k in [sorted(keys)[0],(0,0)]:
        c=cases[k[0]];original=next(r for r in c['original_seed_metrics'] if r['seed']==k[1])
        probes.append({'source':'selection','case':k[0],'scheme':c['scheme'],'param':c['point'],'seed':k[1],
            'config':dataclasses.asdict(configuration(c['config'])),'actual':selected[k],
            'original':{c['metric']:original['outcome'],'symbols':original['symbols']}})
    write_json(out/'probe_plan.json',{'cases':probes,'variants':['default-repeat1','default-repeat2','scalar-exp','no-simd'],
        'maximum_missions':24,'selection_rule':'First lexicographic mismatching key per stage/scheme, first selection mismatch, case0seed0 matching control',
        'role':'Published-evaluation diagnostic only; not new-method performance or calibration','per_job_seconds':120})
    for variant in ['default-repeat1','default-repeat2','scalar-exp','no-simd']:
        env=os.environ.copy()
        if variant=='no-simd':env['NPY_DISABLE_CPU_FEATURES']='AVX512F,AVX2,FMA3'
        subprocess.run([sys.executable,__file__,'probe','--plan',str(out/'probe_plan.json'),'--variant',variant],env=env,check=True,timeout=850)
    summaries=[]
    for p in sorted(out.glob('probe-*.json')):summaries+=json.loads(p.read_text())
    write_json(out/'diagnostic_summary.json',{'missions':len(summaries),'records':summaries,'no_algorithm_replacement':'scalar-exp is an isolated numerical-sensitivity intervention only; strict outputs retained'})
    print(json.dumps([{'stage':r['stage'],'file':r['file'],'status':r['status'],'compared':r.get('compared_common_keys'),'mismatches':r.get('mismatch_records')} for r in reports]),flush=True)
    print(json.dumps([{'source':r['source'],'scheme':r['scheme'],'variant':r['variant'],'matches_current':not r['different_from_current'],'matches_published':not r['different_from_published']} for r in summaries]),flush=True)


def probe(out,plan,variant):
    import numpy as np
    from gosc import Config
    from gosc.simulator import Simulation
    if variant=='scalar-exp':
        from gosc.channel import Channel
        original=Channel.success_prob
        def scalar(self,rate,snr_mean,n=None):
            if self.fbl or self.csit:return original(self,rate,snr_mean,n)
            value=-(2.0**np.asarray(rate)-1.0)/snr_mean
            if np.ndim(value)==0:return np.float64(math.exp(float(value)))
            return np.array([math.exp(float(v)) for v in value.reshape(-1)]).reshape(value.shape)
        Channel.success_prob=scalar
    rows=[]
    for index,item in enumerate(json.loads(Path(plan).read_text())['cases']):
        import signal
        def alarm(signum,frame):raise TimeoutError('Diagnostic120s budget')
        signal.signal(signal.SIGALRM,alarm);signal.alarm(120)
        started=time.monotonic();cfg=dict(item['config']);cfg['rates']=tuple(cfg['rates']);cfg['llm_agents']=tuple(cfg['llm_agents'])
        sim=Simulation(Config(**cfg),item['scheme'],item['seed']);sim.scheme.log=[] if hasattr(sim.scheme,'log') else None
        world={'victims':sorted(map(int,sim.world.victims)),'starts':[list(map(int,a.pos)) for a in sim.agents]}
        result=sim.run();result.pop('curve');signal.alarm(0)
        keys=['completion_time','completed','found','saved_fraction','symbols','bits','delivered_bits','dl_symbols','false_declarations','confirm_latency']
        trace=[]
        for groups,chosen,price,budget in (sim.scheme.log or []):
            opts=[[{'rate':o.rate,'bits':o.bits,'symbols':o.symbols,'value_hex':float(o.value).hex(),'n_records':o.n_records} for o in g.options] for g in groups]
            choices=[(next(i for i,g in enumerate(groups) if g is group),o.rate,o.bits,o.symbols,o.n_records) for group,o in chosen]
            trace.append({'options':opts,'chosen':choices,'price':price,'budget':budget})
        trace_path=out/f'trace-{variant}-{index}.json'
        write_json(trace_path,trace)
        rows.append({'source':item['source'],'scheme':item['scheme'],'param':item['param'],'seed':item['seed'],'variant':variant,
            'numpy':np.__version__,'disabled_cpu_features':os.environ.get('NPY_DISABLE_CPU_FEATURES'),
            'world_sha256':hashlib.sha256(json.dumps(world,sort_keys=True).encode()).hexdigest(),'result':result,
            'different_from_current':[k for k in keys if k in item['actual'] and not equal(result.get(k),item['actual'][k])],
            'different_from_published':[k for k in keys if k in item['original'] and not equal(result.get(k),item['original'][k])],
            'trace_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest(),'trace_decisions':len(trace),'wall_s':time.monotonic()-started})
    write_json(out/f'probe-{variant}.json',rows)


def main():
    require_hpc();p=argparse.ArgumentParser();p.add_argument('mode',choices=['audit','probe']);p.add_argument('--plan');p.add_argument('--variant');a=p.parse_args()
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    if a.mode=='audit':audit(out)
    else:probe(out,a.plan,a.variant)


if __name__=='__main__':main()
