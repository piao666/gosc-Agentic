"""Independent public selection0-99, freeze, then fresh3000-3099 verification."""
import argparse
import dataclasses
import hashlib
import json
import math
from multiprocessing import Pool
import os
from pathlib import Path

import numpy as np
from gosc import Config
from gosc.simulator import Simulation


def configuration(raw):
    cfg=dict(raw);cfg['rates']=tuple(cfg['rates']);cfg['llm_agents']=tuple(cfg['llm_agents'])
    return Config(**cfg)


def job(argument):
    case,seed=argument
    cfg=configuration(case['config']);sim=Simulation(cfg,case['scheme'],seed)
    world={'victims':sorted(map(int,sim.world.victims)),
           'starts':[[int(v) for v in a.pos] for a in sim.agents],
           'deadlines':{str(k):int(v) for k,v in sim.world.deadline.items()}}
    world_hash=hashlib.sha256(json.dumps(world,sort_keys=True).encode()).hexdigest()
    result=sim.run();result.pop('curve',None)
    return {'case':case['case'],'setting':case['setting'],'family':case['family'],'point':case['point'],
            'scheme':case['scheme'],'seed':seed,'world_start_sha256':world_hash,**result}


def freeze(cases,rows):
    frozen={};summaries=[]
    for setting in dict.fromkeys(c['setting'] for c in cases):
        meta=[c for c in cases if c['setting']==setting];metric=meta[0]['metric']
        genie=next(c for c in meta if c['family']=='genie_reference')
        references=[r[metric] for r in rows if r['case']==genie['case']]
        assert len(references)==100
        assert {r['seed'] for r in rows if r['case']==genie['case']}==set(range(100))
        target=(1.25 if metric=='completion_time' else .9)*float(np.mean(references))
        entry={'metric':metric,'target':target}
        for family in ['gosc','periodic']:
            viable=[]
            for c in meta:
                if c['family']!=family:continue
                selected=sorted([r for r in rows if r['case']==c['case']],key=lambda r:r['seed'])
                assert len(selected)==100 and {r['seed'] for r in selected}==set(range(100))
                outcome=float(np.mean([r[metric] for r in selected]));symbols=float(np.mean([r['symbols'] for r in selected]))
                meets=outcome<=target if metric=='completion_time' else outcome>=target
                summaries.append({'setting':setting,'case':c['case'],'family':family,'scheme':c['scheme'],
                    'point':c['point'],'mean_outcome':outcome,'mean_symbols':symbols,'target':target,'meets':bool(meets)})
                if meets:viable.append((symbols,c,selected))
            winner=min(viable,key=lambda v:v[0]) if viable else None
            if winner:
                y,c,selected=winner
                entry[family]={'scheme':c['scheme'],'point':c['point'],'config':c['config'],'eval_ksym':y/1000}
            else:entry[family]=None
        frozen[setting]=entry
    return frozen,summaries


def run_cases(cases,seeds,out):
    keys={(c['case'],s) for c in cases for s in seeds}
    raw=out/'selection_episodes.jsonl';raw.touch(exist_ok=False);rows=[]
    with Pool(2) as pool,raw.open('a',encoding='utf-8') as stream:
        compact=[{k:v for k,v in c.items() if k!='original_seed_metrics'} for c in cases]
        for r in pool.imap_unordered(job,[(c,s) for s in seeds for c in compact],chunksize=1):
            assert (r['case'],r['seed']) in keys;keys.remove((r['case'],r['seed']))
            stream.write(json.dumps(r)+'\n');stream.flush();rows.append(r)
    assert not keys
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['select','fresh','sensitivity','sensitivity-fresh','genie'],required=True)
    args=p.parse_args();out=Path(os.environ['GOSC_OUTPUT_DIR']);root=Path(os.environ['REPRO_PROJECT_ROOT']);work=Path.cwd()
    def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    original=json.loads((root/'results/rev_validation.json').read_text())
    catalog=json.loads((root/'research/sync/runs/hpc-remaining-inventory-20261019/outputs/selection_catalog.json').read_text())
    cases=[{**c,'case':i} for i,c in enumerate(catalog)]
    if args.mode=='select':
        save(out/'candidate_configs.json',cases)
        rows=run_cases(cases,list(range(100)),out)
        chosen,summary=freeze(cases,rows)
        mismatches=[];checked=0
        for c in cases:
            expected={r['seed']:r for r in c['original_seed_metrics']}
            for r in rows:
                if r['case']!=c['case'] or r['seed'] not in expected:continue
                checked+=1;e=expected[r['seed']]
                if r[c['metric']]!=e['outcome'] or r['symbols']!=e['symbols']:mismatches.append({'case':c['case'],'seed':r['seed']})
        selected_match=all(chosen[s][f] and chosen[s][f]['scheme']==original[s][f]['scheme'] and chosen[s][f]['point']==original[s][f]['point'] for s in chosen for f in ['gosc','periodic'])
        save(out/'frozen_selection.json',chosen);save(work/'results/independent_selection.json',chosen)
        save(out/'candidate_summary.json',summary)
        save(out/'selection_audit.json',{'status':'verified','missions':len(rows),'candidate_metrics_checked':checked,
            'historical_mismatches':mismatches,'all12_frozen_points_match':selected_match,
            'calibration_status':'upstream_procedure_not_provided','selection_seeds':[0,99],'fresh_seeds_used_for_selection':False})
        search=[];rescue=[]
        for c in cases:
            selected=[r for r in rows if r['case']==c['case']]
            if c['family']=='genie_reference' and c['setting'].startswith('search'):
                search += [{**r,'param':c['setting'].split('-',1)[1]} for r in selected]
            if c['setting'].startswith('rescue'):
                label=c['setting'].split('-',1)[1]+'/ref' if c['family']=='genie_reference' else c['point']
                rescue += [{**r,'param':label} for r in selected]
        save(work/'results/rev_genie_ref.json',{'rows':search});save(work/'results/rev_rescue.json',{'rows':rescue})
    elif args.mode in ['fresh','sensitivity-fresh']:
        prefix='independent' if args.mode=='fresh' else 'sensitivity'
        chosen=json.loads((work/f'results/{prefix}_selection.json').read_text());fresh_cases=[]
        for setting,entry in chosen.items():
            for family in ['gosc','periodic']:
                c=entry[family]
                if c:fresh_cases.append({'case':len(fresh_cases),'setting':setting,'family':family,'point':c['point'],'scheme':c['scheme'],'config':c['config'],'metric':entry['metric']})
        save(out/'candidate_configs.json',fresh_cases);rows=run_cases(fresh_cases,list(range(3000,3100)),out)
        result={}
        for setting,entry in chosen.items():
            value={'metric':entry['metric'],'target':entry['target']}
            for family in ['gosc','periodic']:
                c=next((v for v in fresh_cases if v['setting']==setting and v['family']==family),None)
                if c is None:value[family]=None;continue
                selected=sorted([r for r in rows if r['case']==c['case']],key=lambda r:r['seed'])
                metric=entry['metric'];m=np.array([r[metric] for r in selected],float);y=np.array([r['symbols'] for r in selected],float)
                value[family]={'point':c['point'],'scheme':c['scheme'],'eval_ksym':entry[family]['eval_ksym'],
                    'fresh_metric':float(m.mean()),'fresh_metric_ci':float(1.96*m.std(ddof=1)/10),
                    'fresh_ksym':float(y.mean()/1000),'fresh_ksym_ci':float(1.96*y.std(ddof=1)/10/1000),
                    'meets_target':bool(m.mean()<=entry['target'] if metric=='completion_time' else m.mean()>=entry['target']),
                    'metric_per_seed':m.tolist(),'ksym_per_seed':(y/1000).tolist()}
            if value.get('gosc') and value.get('periodic'):
                a=np.array(value['periodic']['ksym_per_seed']);g=np.array(value['gosc']['ksym_per_seed']);idx=np.random.default_rng(0).integers(0,100,(4000,100));ratio=a[idx].mean(1)/g[idx].mean(1)
                value['ratio']=[float(a.mean()/g.mean()),*map(float,np.percentile(ratio,[2.5,97.5]))]
            result[setting]=value
        save(out/'fresh_validation.json',result)
        if args.mode=='fresh':save(work/'results/rev_validation.json',result)
    elif args.mode=='sensitivity':
        initial=root/'research/sync/runs/ordered-selection-20261019/outputs/selection_episodes.jsonl'
        rows=[json.loads(line) for line in initial.read_text().splitlines()]
        added=[]
        for c in list(cases):
            if c['family']=='genie_reference' and c['setting'].startswith('search'):
                added.append({**c,'case':len(cases)+len(added),'family':'periodic','scheme':'sem_ra',
                    'point':c['setting'].split('-',1)[1]+'/k16','config':{**c['config'],'sem_interval':16},'original_seed_metrics':[]})
        save(out/'candidate_configs.json',added);rows+=run_cases(added,list(range(100)),out)
        chosen,summary=freeze(cases+added,rows);save(out/'frozen_selection.json',chosen)
        save(out/'candidate_summary.json',summary);save(work/'results/sensitivity_selection.json',chosen)
    else:
        references=[c for c in cases if c['family']=='genie_reference']
        save(out/'candidate_configs.json',references);run_cases(references,list(range(3000,3100)),out)


if __name__=='__main__':main()
