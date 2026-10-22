"""HPC-only bounded cost probes; never launches the full A1 campaign."""
from pathlib import Path
import argparse
import csv
import dataclasses
import hashlib
import json
import math
import os
import re
import signal
import sys

from hpc_runs import ROOT, require_hpc, write_json
from hpc_reproduce import snapshot, copy_environment
from r4_pilot import canonical, fingerprint, run_jobs, validate_payload

sys.path.insert(0, str(ROOT))
PLAN = ROOT/'research/protocols/r4_cost_probe_v1.json'
BASE_HEAD = '876fc523b113b3b65e19f0b730f1573ccc2ee17f'
PRIOR_RUN = 'hpc-r4-a0-pilot-retry1-20261019'
EXPECTED_SETTINGS = [
    {'name':'search-K10','base_config':{'n_agents':10},'arms':[
        {'scheme':'gosc','point':'K10/eta0.0003','overrides':{'energy_price':3e-4}},
        {'scheme':'sem_ras','point':'K10/k4/th0.05','overrides':{'sem_interval':4,'filter_eps':0.05}}]},
    {'name':'search-clustered','base_config':{'victim_layout':'clustered'},'arms':[
        {'scheme':'gosc','point':'clustered/eta3e-05','overrides':{'energy_price':3e-5}},
        {'scheme':'sem_ras','point':'clustered/k4/th0.2','overrides':{'sem_interval':4,'filter_eps':0.2}}]},
    {'name':'rescue-W50','base_config':{'task':'rescue','deadline_min':60,'deadline_max':180,'symbols_per_slot':50},'arms':[
        {'scheme':'gosc','point':'W50/eta0.0001','overrides':{'energy_price':1e-4}},
        {'scheme':'sem_ras','point':'rescue-W50/k2/th1.0','overrides':{'sem_interval':2,'filter_eps':1.0}}]},
    {'name':'rescue-snr-5','base_config':{'task':'rescue','deadline_min':60,'deadline_max':180,'snr_ref_db':-5},'arms':[
        {'scheme':'gosc','point':'snr-5/eta0.0001','overrides':{'energy_price':1e-4}},
        {'scheme':'sem_ras','point':'rescue-snr-5/k2/th1.0','overrides':{'sem_interval':2,'filter_eps':1.0}}]},
]
FULL_GROUPS = {(s['name'],a['scheme']) for s in EXPECTED_SETTINGS for a in s['arms']} | {
    ('search-W100','gosc'),('search-W100','sem_raf'),('rescue-W100','gosc'),('rescue-W100','sem_ras')}


def expand_plan(plan):
    if (plan['head'],plan['seeds'],plan['settings'],plan['workers_max'],plan['worker_threads'],
        plan['per_episode_timeout_seconds'],plan['campaign_budget_seconds'],plan['planned_missions'],
        plan['prior_pilot_run']) != (BASE_HEAD,[9010,9011,9012],EXPECTED_SETTINGS,2,1,120,600,24,PRIOR_RUN):
        raise ValueError('Cost probe scope differs from the authorized 24 missions')
    from gosc import Config
    jobs=[]
    for seed in plan['seeds']:
        for scene in plan['settings']:
            for arm in scene['arms']:
                cfg=Config().with_(**(scene['base_config']|arm['overrides']))
                config=json.loads(json.dumps(dataclasses.asdict(cfg)))
                jobs.append({'job_id':f"{scene['name']}-{seed}-{arm['scheme']}",'setting':scene['name'],
                             'seed':seed,'scheme':arm['scheme'],'config':config,'config_sha256':fingerprint(config)})
    if len(jobs)!=24 or len({j['job_id'] for j in jobs})!=24:raise ValueError('Duplicate/missing jobs')
    return jobs


def check_frozen(plan, frozen):
    for scene in plan['settings']:
        for arm in scene['arms']:
            source=frozen[scene['name']]['gosc' if arm['scheme']=='gosc' else 'periodic']
            if source['scheme']!=arm['scheme'] or source['point']!=arm['point']:
                raise ValueError('Frozen author point mismatch: '+scene['name'])


def load_rows(folder):
    return [json.loads(line) for line in (folder/'episodes.jsonl').read_text().splitlines()]


def group_costs(rows, source_run):
    groups=[]
    for setting,scheme in sorted({(r['setting'],r['scheme']) for r in rows if r['scheme']!='genie'}):
        group=[r for r in rows if r['setting']==setting and r['scheme']==scheme]
        if any(r['execution_status']!='completed' for r in group):raise ValueError('Incomplete cost sample')
        n=len(group)
        resources=[r['output']['worker_resources'] for r in group]
        groups.append({'setting':setting,'scheme':scheme,'n':n,'source_run':source_run,
            'mean_worker_wall_seconds':math.fsum(r['process_elapsed_seconds'] for r in group)/n,
            'max_worker_wall_seconds':max(r['process_elapsed_seconds'] for r in group),
            'mean_worker_cpu_seconds':math.fsum(v['cpu_user_seconds']+v['cpu_system_seconds'] for v in resources)/n,
            'max_single_worker_rss_kib':max(v['max_rss_kib'] for v in resources),
            'mean_raw_record_bytes':math.fsum(len(json.dumps(r,ensure_ascii=False,allow_nan=False).encode())+1 for r in group)/n})
    return groups


def budget_projection(groups, scheduling_factor):
    if len(groups)!=12 or {(g['setting'],g['scheme']) for g in groups}!=FULL_GROUPS:
        raise ValueError('All twelve frozen setting/arm cost groups are required')
    if not math.isfinite(scheduling_factor) or scheduling_factor<1:raise ValueError('Invalid scheduling factor')
    # Weight each setting/arm by its planned 100 jobs, not by unequal probe N.
    wall=100*math.fsum(g['mean_worker_wall_seconds'] for g in groups)/2*scheduling_factor
    maximum=100*math.fsum(g['max_worker_wall_seconds'] for g in groups)/2*scheduling_factor
    recommended=math.ceil((max(3*wall,maximum)+120)/60)*60
    return {'main_missions':1200,'settings':6,'arms_per_setting':2,'seeds':[3000,3099],
        'workers_max':2,'worker_threads':1,'scheduling_factor':scheduling_factor,
        'estimated_worker_cpu_seconds':100*math.fsum(g['mean_worker_cpu_seconds'] for g in groups),
        'estimated_campaign_wall_seconds':wall,'observed_per_group_max_scenario_wall_seconds':maximum,
        'recommended_campaign_cap_seconds':recommended,'per_episode_timeout_seconds':120,
        'budget_rule':'Round up to minutes: max(3 x group-mean wall estimate, group-max scenario) + 120s; heuristic, not confidence bound.',
        'estimated_raw_episodes_bytes':100*math.fsum(g['mean_raw_record_bytes'] for g in groups),
        'raw_output_budget_bytes':max(10485760,math.ceil(3*100*math.fsum(g['mean_raw_record_bytes'] for g in groups))),
        'largest_observed_worker_rss_kib':max(g['max_single_worker_rss_kib'] for g in groups),
        'memory_limit_bytes':25769803776,'gpu_required':False,'genie_missions_included':False,
        'scope_exclusions':['optional 600 Genie','candidate search B','frontier C','calibration','LLM','training','sync and audit time'],
        'limitations':'N=3 in four settings and N=10 in two; host contention/other seeds may change costs. Worker RSS is not whole-container peak.',
        'full_campaign_status':'not_started','training_status':'not_started'}


def summarize(result, jobs, out, run_id):
    rows=result['records']
    keys=[r['job_id'] for r in rows]
    complete=len(rows)==24 and set(keys)=={j['job_id'] for j in jobs} and all(r['execution_status']=='completed' for r in rows)
    pairs=[]
    for setting,seed in sorted({(r['setting'],r['seed']) for r in rows}):
        pair=[r for r in rows if r['setting']==setting and r['seed']==seed]
        good=len(pair)==2 and all(r['execution_status']=='completed' for r in pair)
        if good and len({r['output']['world_start_sha256'] for r in pair})!=1:raise ValueError('Unpaired initial world')
        pairs.append({'setting':setting,'seed':seed,'complete_pair':good})
    value={'status':'complete' if complete else 'partial_or_failed','planned_missions':24,
           'execution_counts':{s:sum(r['execution_status']==s for r in rows) for s in ['completed','failed','timeout','interrupted']},
           'pairs':pairs,'campaign_wall_seconds':result['elapsed_seconds'],'max_active_workers':result['max_active_workers'],
           'stop_reason':result['stop_reason'],'performance_inference':'None; costs only, no parameter selection'}
    if complete:
        groups=group_costs(rows,run_id)
        previous=ROOT/'research/sync/runs'/PRIOR_RUN
        if json.loads((previous/'status.json').read_text())['status']!='completed':raise ValueError('Prior pilot incomplete')
        oldrows=load_rows(previous/'outputs')
        oldsummary=json.loads((previous/'outputs/pilot_summary.json').read_text())
        groups+=group_costs(oldrows,PRIOR_RUN)
        factors=[result['elapsed_seconds']*2/math.fsum(r['process_elapsed_seconds'] for r in rows),
                 oldsummary['costs']['campaign_wall_seconds']*2/math.fsum(r['process_elapsed_seconds'] for r in oldrows)]
        value['cost_groups']=groups
        value['scheduling_factors_measured']=factors
        value['budget']=budget_projection(groups,max(1,*factors))
        write_json(out/'a1_budget.json',value['budget'])
        with (out/'cost_groups.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(groups[0]));writer.writeheader();writer.writerows(groups)
    write_json(out/'cost_probe_summary.json',value)
    print(json.dumps(value),flush=True)
    return complete


def execute():
    out=Path(os.environ['GOSC_OUTPUT_DIR']);run_dir=Path(os.environ['GOSC_RUN_DIR'])
    if out.resolve()!=(run_dir/'outputs').resolve() or run_dir.parent!=ROOT/'research/sync/runs':raise ValueError('Invalid output area')
    before=snapshot();plan=json.loads(PLAN.read_text());jobs=expand_plan(plan)
    check_frozen(plan,json.loads((ROOT/'results/rev_validation.json').read_text()))
    for p in (ROOT/'research/sync/runs').glob('*/manifest.json'):
        if p.parent==run_dir:continue
        previous=json.loads(p.read_text())
        if previous['kind']=='simulation' and set(previous.get('seeds',[]))&set(plan['seeds']):
            raise ValueError('Probe seeds already registered; no automatic rerun: '+p.parent.name)
    source=json.loads((ROOT/'.local/hpc-sync/latest_manifest.json').read_text())
    if source['head']!=BASE_HEAD:raise ValueError('Unexpected baseline')
    for entry in source['files']:
        if hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()!=entry['remote_sha256']:
            raise ValueError('Source changed after sync: '+entry['path'])
    python=copy_environment(out)
    write_json(out/'plan_snapshot.json',plan);write_json(out/'jobs.json',jobs)
    write_json(out/'execution_context.json',{'source_sync_id':source['sync_id'],'baseline_head':BASE_HEAD,
        'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),'workers':2,'worker_threads':1,
        'prior_pilot_run':PRIOR_RUN,'scientific_scope':'24 management missions, cost only',
        'worker_entry':'scripts/r4_pilot.py _worker (unchanged verified worker)',
        'full_campaign_started':False,'training_started':False})
    stop={'requested':False}
    def interrupted(signum,frame):stop['requested']=True
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,interrupted)
    try:
        result=run_jobs(jobs,out,ROOT/'.local/r4-cost-workers'/run_dir.name,
            lambda job,spec,dest:[python,ROOT/'scripts/r4_pilot.py','_worker','--job',spec,'--output',dest],
            validate_payload,2,120,600,cancel=lambda:stop['requested'])
        complete=summarize(result,jobs,out,run_dir.name)
    finally:
        after=snapshot();write_json(out/'input_integrity.json',{'before':before,'after':after,'unchanged':before==after})
        if before!=after:raise ValueError('Protected inputs changed')
    return 0 if complete else 1


def audit(run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',run_id) or '..' in run_id:raise ValueError('Invalid run ID')
    run=ROOT/'research/sync/runs'/run_id;source=run/'outputs';out=Path(os.environ['GOSC_OUTPUT_DIR'])
    assert json.loads((run/'status.json').read_text())['status']=='completed'
    rows=load_rows(source);plan=json.loads((source/'plan_snapshot.json').read_text())
    summary=json.loads((source/'cost_probe_summary.json').read_text());context=json.loads((source/'execution_context.json').read_text())
    assert hashlib.sha256(PLAN.read_bytes()).hexdigest()==context['plan_sha256']
    check_frozen(plan,json.loads((ROOT/'results/rev_validation.json').read_text()))
    from gosc import Config
    expected={}
    for scene in plan['settings']:
        for seed in plan['seeds']:
            for arm in scene['arms']:
                expected[(scene['name'],seed,arm['scheme'])]=json.loads(json.dumps(dataclasses.asdict(Config().with_(**(scene['base_config']|arm['overrides'])))))
    assert len(rows)==len(expected)==24 and len({r['job_id'] for r in rows})==24
    for r in rows:
        assert r['execution_status']=='completed' and r['process_exit_code']==0
        assert r['config']==r['output']['config']==expected.pop((r['setting'],r['seed'],r['scheme']))
        validate_payload(r,r['output'])
        assert r['output']['worker_resources']['numeric_library_threads']==1
    assert not expected
    for setting,seed in {(r['setting'],r['seed']) for r in rows}:
        assert len({r['output']['world_start_sha256'] for r in rows if r['setting']==setting and r['seed']==seed})==1
    active=set();maximum=0;starts=0;ends=0
    for line in (source/'events.jsonl').read_text().splitlines():
        event=json.loads(line);key=event['job_id']
        if event['event']=='start':
            assert key not in active;active.add(key);starts+=1;maximum=max(maximum,len(active));assert len(active)<=2
        else:
            assert key in active;active.remove(key);ends+=1
    assert starts==ends==24 and not active
    for entry in json.loads((run/'artifacts.json').read_text())['files']:
        assert hashlib.sha256((run/entry['path']).read_bytes()).hexdigest()==entry['sha256']
    integrity=json.loads((source/'input_integrity.json').read_text());assert integrity['before']==integrity['after'] and integrity['unchanged']
    for rel,digest in integrity['before'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest
    # Independently recompute all twelve means and the equal-weight 100-seed projection.
    allrows=rows+load_rows(ROOT/'research/sync/runs'/PRIOR_RUN/'outputs')
    for group in summary['cost_groups']:
        selected=[r for r in allrows if r['setting']==group['setting'] and r['scheme']==group['scheme']]
        assert len(selected)==group['n']
        for field,key in [('process_elapsed_seconds','mean_worker_wall_seconds')]:
            assert math.isclose(math.fsum(r[field] for r in selected)/len(selected),group[key],rel_tol=1e-12)
        cpu=math.fsum(r['output']['worker_resources']['cpu_user_seconds']+r['output']['worker_resources']['cpu_system_seconds'] for r in selected)/len(selected)
        assert math.isclose(cpu,group['mean_worker_cpu_seconds'],rel_tol=1e-12)
    assert {(g['setting'],g['scheme']) for g in summary['cost_groups']}==FULL_GROUPS
    budget=json.loads((source/'a1_budget.json').read_text())
    assert budget==summary['budget'] and budget['main_missions']==1200 and budget['full_campaign_status']=='not_started'
    estimate=50*math.fsum(g['mean_worker_wall_seconds'] for g in summary['cost_groups'])*budget['scheduling_factor']
    assert math.isclose(estimate,budget['estimated_campaign_wall_seconds'],rel_tol=1e-12)
    value={'status':'verified','cost_probe_run':run_id,'unique_missions':24,'complete_pairs':12,
        'worker_starts':starts,'worker_terminals':ends,'max_concurrency':maximum,'cost_groups_verified':12,
        'frozen_configs_match':True,'protected_inputs_unchanged':True,'budget_weighting_verified':True,
        'new_simulations_in_audit':0,'full_campaign_started':False,'training_started':False}
    write_json(out/'cost_probe_audit.json',value);print(json.dumps(value),flush=True)
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('validate');sub.add_parser('execute')
    p=sub.add_parser('audit');p.add_argument('--probe-run',required=True)
    args=parser.parse_args();require_hpc()
    if args.action=='validate':
        plan=json.loads(PLAN.read_text());jobs=expand_plan(plan)
        check_frozen(plan,json.loads((ROOT/'results/rev_validation.json').read_text()))
        print(json.dumps({'planned_missions':len(jobs),'scientific_missions_started':0}));return 0
    if args.action=='audit':return audit(args.probe_run)
    return execute()


if __name__=='__main__':raise SystemExit(main())
