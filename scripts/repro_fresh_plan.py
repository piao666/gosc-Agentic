"""Plan native realistic fresh jobs from frozen grid results without any simulation."""
import dataclasses
import hashlib
import json
from collections import Counter

def plan(work):
    from experiments import validate_realistic as v
    rows={n:v.load_jsonl(n) for n in ['noise','overhead','shared']};jobs=[]
    def add(track,setting,family,scheme,cfg,point,**meta):
        payload=dataclasses.asdict(cfg);sha=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        jobs.append({'track':track,'setting':setting,'family':family,'scheme':scheme,'point':point,'config_sha256':sha,'seeds':[3000,3099],'missions':100,**meta})
    # Same fixed selection functions and exclusions as the native entry point.
    for st in v.HEADLINE:
        metric,target=v.reference(st)
        for arm,(scheme,kw) in v.ARMS.items():
            if arm=='exact' and not st.startswith('rescue'):continue
            selected=v.select(rows['noise'],st,'gosc',metric,target,arm=arm)
            if selected:
                _,sch,p=selected;add('noise',st,'gosc',sch,v.SETTINGS[st].with_(**kw,**v.point_kw(p)),p,arm=arm)
    frozen=v.main_frozen()
    for st in v.HEADLINE:
        metric,target=v.reference(st)
        for h in [0,16,32,64]:
            base=v.SETTINGS[st].with_(overhead_bits=h)
            for family in ['gosc','periodic']:
                if h==0:sch,p=frozen[st][family]['scheme'],frozen[st][family]['point'].split('/',1)[1]
                else:
                    eligible=[r for r in rows['overhead'] if not (st.startswith('rescue') and r['family']=='gosc' and r['point'] in ['eta0.0003','eta0.001'])]
                    selected=v.select(eligible,st,family,metric,target,H=h)
                    if selected is None:continue
                    _,sch,p=selected
                add('overhead',st,family,sch,base.with_(**v.point_kw(p)),p,H=h)
    for h in [0,32]:
        for scheme in ['report','raw','nl','sem']:add('overhead','search-W100','conventional',scheme,v.SETTINGS['search-W100'].with_(overhead_bits=h),'ref',H=h)
    for st,(cfg,budget) in v.SHARED.items():
        metric,target=v.reference(st);c=cfg.with_(shared_budget=budget,symbols_per_slot=budget)
        for family in ['gosc','periodic']:
            selected=v.select(rows['shared'],st,family,metric,target)
            if selected:
                _,sch,p=selected;add('shared',st,family,sch,c.with_(**v.point_kw(p)),p)
    return {'seeds':[3000,3099],'missions':sum(r['missions'] for r in jobs),'maximum_before_grid_selection':10300,'jobs':jobs,'selection_uses_fresh_outcomes':False,'scope':'Only points meeting native0-99 targets; missing targets remain infeasible, no replacement'}

def audit(out,expected):
    actual=Counter()
    for p in out.glob('pool-plans.jsonl'):
        for line in p.read_text().splitlines():
            record=json.loads(line)
            for cfg,scheme,seed in record['arguments']:actual[(cfg['config_sha256'],scheme,seed)]+=1
    wanted=Counter((r['config_sha256'],r['scheme'],seed) for r in expected['jobs'] for seed in range(3000,3100))
    if actual!=wanted:raise RuntimeError('Native fresh executed-job plan differs from frozen pre-stage catalog')
    return {'expected_missions':expected['missions'],'actual_planned_missions':sum(actual.values()),'exact_configs_schemes_seeds_match':True}
