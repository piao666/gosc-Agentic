"""Prospective bounded receiver-information headroom pilot; not a learned method."""
import argparse,collections,dataclasses,hashlib,json,multiprocessing as mp,os,signal,sys,time
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
from gosc import Config
from extensions.receiver_diagnostic import EventSimulation,world_fingerprint

FAMILIES=['public_tom','m0_bits','m0_aoi','m0_periodic','oracle_private','oracle_positions','oracle_both']
SIMPLE=['m0_bits','m0_aoi','m0_periodic']
CALIB=list(range(12000000,12000008));TEST=list(range(13000000,13000020));GUARD=list(range(14000000,14000003))
TRAIN_RESERVED=list(range(11000000,11000100))
def save(path,x):path.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def read(path):return json.loads(path.read_text())
def lines(path):
    with path.open() as f:
        for l in f:
            if l.strip():yield json.loads(l)
def catalog():
    from experiments.run_realistic import PERIODIC
    cases=[]
    def add(setting,family,scheme,cfg,label):
        cases.append({'id':len(cases),'setting':setting,'family':family,'scheme':scheme,'config':dataclasses.asdict(cfg),'label':label})
    for W in [100,50]:
        setting='search-W'+str(W);base=Config().with_(symbols_per_slot=W)
        for family,scheme,oracle in [('public_tom','gosc',False),('oracle_private','diag_receiver_private',True),
                 ('oracle_positions','diag_receiver_positions',True),('oracle_both','diag_receiver_both',True)]:
            for eta in [1e-6,3e-6,1e-5,3e-5,1e-4,3e-4]:
                add(setting,family,scheme,base.with_(energy_price=eta,tom_oracle=oracle),'eta'+str(eta))
        for family,scheme,etas in [('m0_bits','gosc_bits',[0,.003,.01,.03,.1,.3,1,3]),
                                  ('m0_aoi','gosc_aoi',[0,.0003,.001,.003,.01,.03,.1,.3])]:
            for eta in etas:add(setting,family,scheme,base.with_(energy_price=eta),'eta'+str(eta))
        for scheme,k,th in PERIODIC:
            kw={'sem_interval':k}
            if th is not None:kw['filter_eps']=th
            add(setting,'m0_periodic',scheme,base.with_(**kw),'k'+str(k)+'/th'+str(th))
    return cases
def cfg_from(raw):
    raw=dict(raw);raw['rates']=tuple(raw['rates']);raw['llm_agents']=tuple(raw['llm_agents']);return Config(**raw)

def prepare(out):
    ints=set();fingerprints=set();paths=[]
    def walk(x):
        if isinstance(x,bool):return
        if isinstance(x,int):ints.add(x)
        elif isinstance(x,list):
            for v in x:walk(v)
        elif isinstance(x,dict):
            for v in x.values():walk(v)
    for p in (ROOT/'research/sync/runs').glob('*/outputs/pool-plans.jsonl'):
        paths.append(p.relative_to(ROOT).as_posix())
        for row in lines(p):walk(row.get('arguments',[]))
    for p in (ROOT/'research/sync/runs').glob('*/outputs/selection_episodes.jsonl'):
        for row in lines(p):
            if 'seed' in row:ints.add(row['seed'])
            if row.get('world_start_sha256'):fingerprints.add(row['world_start_sha256'])
    reserved=TRAIN_RESERVED+CALIB+TEST+GUARD
    collisions=sorted(set(reserved)&ints);assert not collisions,collisions
    cases=catalog();worlds={}
    for W in [100,50]:
        for seed in CALIB+TEST+GUARD:
            sim=EventSimulation(Config().with_(symbols_per_slot=W),'gosc',seed)
            assert sim.input_world_sha256 not in fingerprints,'Known world collision'
            worlds[str(W)+'/'+str(seed)]=sim.input_world_sha256
    source_paths=['extensions/receiver_diagnostic.py','scripts/repro_receiver_pilot.py',
                  'tests_ext/test_receiver_diagnostic.py','research/protocols/receiver_headroom_pilot_v1.md']
    source_paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'gosc').glob('*.py')]
    protocol={'schema_version':1,'status':'frozen_before_pilot_outcomes','exploratory':True,
       'source_sha256':{p:digest(ROOT/p) for p in source_paths},'cases':cases,
       'calibration_seeds':CALIB,'test_seeds':TEST,'guard_seeds':GUARD,'train_reserved_not_used':TRAIN_RESERVED,
       'world_fingerprints':worlds,'registry_check':{'input_catalogs':paths,'conservative_integer_ban_count':len(ints),
       'known_world_fingerprints':len(fingerprints),'seed_collisions':collisions},
       'mean_ul_calibration_cap':10000,'selection':'Within each family, minimum mean completion_time among candidates with meanUL<=10000; tie meanUL then id. Choose strongest simple family on calibration only.',
       'max_wall_seconds':1800,'per_job_seconds':90,'workers':2,'numeric_threads':1,
       'max_calibration_missions':len(cases)*len(CALIB),'max_validation_missions':2*len(FAMILIES)*len(TEST),
       'primary_family_comparisons':6,'primary_endpoints_per_comparison':2,'bonferroni_family':12,
       'alpha':.05,'bootstrap_resamples':20000,'stat_seed':15999999,
       'minimum_mean_task_gain_slots':3,'maximum_cost_ratio_upper_ci':1.05,
       'task_effect':'M0star completion slots minus privileged completion slots; failed missions retainmax_steps',
       'cost':'Logged base-simulator UL+DL, ratio privileged/M0star; oracle state acquisition free and disclosed',
       'oracle_not_deployable':True,'oracle_not_mathematical_optimal_bound':True,
       'external_randomness':'Sense U(seed,201,t,agent,globalcell);fading(seed,202,t,agent);planner noise(seed,203,t,agent,cell). Same seed same world; no branch-consumption alignment assumption.',
       'new_llm_calls':0,'training':False,'scope':'Two original search settings W100/W50; Planner only, ideal DL; not author exact replay or LLM-generalization evidence'}
    save(out/'protocol.json',protocol)
    save(out/'preflight.json',{'cases':len(cases),'calibration_missions':len(cases)*len(CALIB),'validation_cap':protocol['max_validation_missions'],
       'seed_conflicts':collisions,'world_identity_checks':len(worlds),'training_seeds_used':False})

def job(arg):
    case,seed=arg;started=time.monotonic();cpu=time.process_time()
    def alarm(signum,frame):raise TimeoutError('Pilot per job90s cap')
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,90)
    try:
        sim=EventSimulation(cfg_from(case['config']),case['scheme'],seed)
        result=sim.run();result.pop('curve')
        row={'status':'completed','case_id':case['id'],'setting':case['setting'],'family':case['family'],'seed':seed,
             'world_sha256':sim.input_world_sha256,'first_slot_potential_field_hashes':sim.event_field_hashes,'result':result}
    except Exception as e:row={'status':'failed','case_id':case['id'],'seed':seed,'error':repr(e)}
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    row.update(wall_seconds=time.monotonic()-started,cpu_seconds=time.process_time()-cpu)
    return row

def phase(out,name,cases,seeds,protocol,deadline):
    rows=[]
    args=[(case,seed) for seed in seeds for case in cases]
    with mp.get_context('fork').Pool(2,maxtasksperchild=64) as pool,(out/(name+'.jsonl')).open('x') as f:
        it=pool.imap_unordered(job,args,chunksize=1)
        for i in range(len(args)):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('Pilot global30min cap')
            row=it.next(timeout=remaining);f.write(json.dumps(row)+'\n');f.flush()
            if row['status']!='completed':raise RuntimeError(row)
            W=cfg_from(next(c for c in cases if c['id']==row['case_id'])['config']).symbols_per_slot
            assert row['world_sha256']==protocol['world_fingerprints'][str(W)+'/'+str(row['seed'])]
            rows.append(row)
            if (i+1)%25==0:print(name,i+1,'/',len(args),flush=True)
    return rows

def pilot(out,protocol_path):
    p=read(protocol_path)
    for name,h in p['source_sha256'].items():assert digest(ROOT/name)==h,('Source changed',name)
    deadline=time.monotonic()+p['max_wall_seconds'];cases=p['cases']
    calibration=phase(out,'calibration',cases,p['calibration_seeds'],p,deadline)
    selected={};descriptions=[]
    for setting in ['search-W100','search-W50']:
        selected[setting]={}
        for fam in FAMILIES:
            options=[]
            for case in cases:
                if case['setting']!=setting or case['family']!=fam:continue
                rows=[r for r in calibration if r['case_id']==case['id']]
                assert len(rows)==len(CALIB)
                T=sum(r['result']['completion_time'] for r in rows)/len(rows)
                UL=sum(r['result']['symbols'] for r in rows)/len(rows)
                value={'case':case,'calibration_mean_T':T,'calibration_mean_UL':UL,'eligible':UL<=p['mean_ul_calibration_cap']}
                descriptions.append(value)
                if value['eligible']:options.append(value)
            selected[setting][fam]=min(options,key=lambda x:(x['calibration_mean_T'],x['calibration_mean_UL'],x['case']['id'])) if options else None
        m0=[selected[setting][f] for f in SIMPLE if selected[setting][f]]
        selected[setting]['m0star']=min(m0,key=lambda x:(x['calibration_mean_T'],x['calibration_mean_UL'],x['case']['id'])) if m0 else None
    freeze={'status':'frozen_before_validation','protocol_sha256':digest(protocol_path),'selected':selected}
    save(out/'calibration_candidate_summary.json',descriptions)
    save(out/'frozen_operating_points.json',freeze)
    wanted={v['case']['id']:v['case'] for s in selected.values() for v in s.values() if v}
    validation=phase(out,'validation',list(wanted.values()),p['test_seeds'],p,deadline)
    import numpy as np
    alpha=p['alpha']/p['bonferroni_family'];rng=np.random.default_rng(p['stat_seed'])
    idx=rng.integers(0,len(TEST),(p['bootstrap_resamples'],len(TEST)))
    summaries=[];effects=[]
    for setting in selected:
        for family,value in selected[setting].items():
            if not value:continue
            ordered=sorted([r for r in validation if r['case_id']==value['case']['id']],key=lambda x:x['seed'])
            assert [r['seed'] for r in ordered]==TEST
            summaries.append({'setting':setting,'family':family,'case_id':value['case']['id'],'label':value['case']['label'],
               'n':len(ordered),'completed':sum(r['result']['completed'] for r in ordered),
               'mean_T':float(np.mean([r['result']['completion_time'] for r in ordered])),
               'mean_UL':float(np.mean([r['result']['symbols'] for r in ordered])),
               'mean_DL':float(np.mean([r['result']['dl_symbols'] for r in ordered]))})
        baseline=selected[setting]['m0star']
        for family in ['oracle_private','oracle_positions','oracle_both']:
            value=selected[setting][family]
            if not baseline or not value:effects.append({'setting':setting,'family':family,'status':'not_comparable_no_calibrated_point'});continue
            a=sorted([r for r in validation if r['case_id']==baseline['case']['id']],key=lambda x:x['seed'])
            b=sorted([r for r in validation if r['case_id']==value['case']['id']],key=lambda x:x['seed'])
            assert [r['seed'] for r in a]==[r['seed'] for r in b]==TEST
            diff=np.array([x['result']['completion_time']-y['result']['completion_time'] for x,y in zip(a,b)],float)
            ca=np.array([r['result']['symbols']+r['result']['dl_symbols'] for r in a],float)
            cb=np.array([r['result']['symbols']+r['result']['dl_symbols'] for r in b],float)
            dboot=diff[idx].mean(1);ratio=cb[idx].mean(1)/ca[idx].mean(1)
            task=[float(diff.mean()),*map(float,np.quantile(dboot,[alpha/2,1-alpha/2]))]
            cost=[float(cb.mean()/ca.mean()),*map(float,np.quantile(ratio,[alpha/2,1-alpha/2]))]
            pass_task=task[0]>=p['minimum_mean_task_gain_slots'] and task[1]>0
            pass_cost=cost[2]<=p['maximum_cost_ratio_upper_ci']
            effects.append({'setting':setting,'family':family,'m0star_family':baseline['case']['family'],'n':len(a),
                'task_gain_slots':task,'cost_ratio_UL_plus_DL':cost,'task_gate':bool(pass_task),'cost_gate':bool(pass_cost),
                'status':'pilot_signal_free_privileged_info_only' if pass_task and pass_cost else 'not_established',
                'interval_level':1-alpha,'acquisition_cost_included':False})
    save(out/'validation_group_statistics.json',summaries)
    save(out/'paired_effects.json',effects)
    save(out/'conclusion.json',{'status':'exploratory_pilot_completed','calibration_missions':len(calibration),'validation_missions':len(validation),
       'comparisons':len(effects),'signals':sum(x['status']=='pilot_signal_free_privileged_info_only' for x in effects),
       'complex_training_go':False,'reason':'Free privileged diagnostic and small held-out panel cannot establish costed deployable receiver estimator',
       'new_llm_calls':0,'labels_for_training_collected':False,'source_unchanged':all(digest(ROOT/n)==h for n,h in p['source_sha256'].items())})
    assert all(digest(ROOT/n)==h for n,h in p['source_sha256'].items())

def main():
    require_hpc();parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['prepare','pilot'],required=True);parser.add_argument('--protocol',type=Path);a=parser.parse_args()
    out=Path(os.environ['GOSC_OUTPUT_DIR'])
    if a.mode=='prepare':prepare(out)
    else:
        assert a.protocol and a.protocol.is_file()
        pilot(out,a.protocol)
if __name__=='__main__':main()
