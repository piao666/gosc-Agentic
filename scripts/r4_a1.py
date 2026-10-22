"""Bounded HPC-only A1 execution, paired analysis and independent bookkeeping audit."""
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

from hpc_runs import ROOT, require_hpc, resource_limits, write_json
from hpc_reproduce import snapshot, copy_environment
from r4_pilot import fingerprint, run_jobs, validate_payload
from r4_cost_probe import EXPECTED_SETTINGS as FOUR_SETTINGS, BASE_HEAD, check_frozen, load_rows

sys.path.insert(0,str(ROOT))
PLAN=ROOT/'research/protocols/r4_a1_plan_v1.json'
EXPECTED_SETTINGS=[
    {'name':'search-W100','base_config':{},'arms':[
        {'scheme':'gosc','point':'W100/eta1e-05','overrides':{'energy_price':1e-5}},
        {'scheme':'sem_raf','point':'W100/k4','overrides':{'sem_interval':4,'filter_eps':0.02}}]},
    *FOUR_SETTINGS[:2],
    {'name':'rescue-W100','base_config':{'task':'rescue','deadline_min':60,'deadline_max':180},'arms':[
        {'scheme':'gosc','point':'W100/eta0.0001','overrides':{'energy_price':1e-4}},
        {'scheme':'sem_ras','point':'rescue-W100/k2/th1.0','overrides':{'sem_interval':2,'filter_eps':1.0}}]},
    *FOUR_SETTINGS[2:]]


def expand_plan(plan):
    if (plan['head'],plan['seeds'],plan['settings'],plan['planned_missions'],plan['workers_max'],
        plan['worker_threads'],plan['per_episode_timeout_seconds'],plan['campaign_budget_seconds'],
        plan['bootstrap_resamples'],plan['analysis_seed']) != (
        BASE_HEAD,list(range(3000,3100)),EXPECTED_SETTINGS,1200,2,1,120,1860,4000,0):
        raise ValueError('A1 scope differs from the authorized frozen 1200 missions')
    from gosc import Config
    jobs=[]
    for seed in plan['seeds']:
        for scene in plan['settings']:
            for arm in scene['arms']:
                config=json.loads(json.dumps(dataclasses.asdict(Config().with_(**(scene['base_config']|arm['overrides'])))))
                assert not config['llm_agents'] and not config['tom_oracle']
                jobs.append({'job_id':f"{scene['name']}-{seed}-{arm['scheme']}",'setting':scene['name'],
                             'seed':seed,'scheme':arm['scheme'],'config':config,'config_sha256':fingerprint(config)})
    if len(jobs)!=1200 or len({j['job_id'] for j in jobs})!=1200:raise ValueError('Missing/duplicate jobs')
    return jobs


def check_ledger(folder,current,plan):
    overlaps=[]
    for p in folder.glob('*/manifest.json'):
        if p.parent.name==current:continue
        previous=json.loads(p.read_text())
        if previous['kind']!='simulation' or not set(previous.get('seeds',[]))&set(plan['seeds']):continue
        status=json.loads((p.parent/'status.json').read_text())
        if not (p.parent.name=='hpc-r3-20261019' and previous['stage']=='R3' and previous['seeds']==[3000]
                and previous['git_commit']==BASE_HEAD and status['status']=='completed'
                and previous['command'][-3:]==['r3','--seed','3000']):
            raise ValueError('Prior overlapping simulation requires inspection; no automatic rerun: '+p.parent.name)
        overlaps.append({'run':p.parent.name,'seeds':[3000],'reason':'Previously disclosed R3 single-mission verification; explicitly repeated in complete frozen reproduction'})
    return overlaps


def run_path(run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',run_id) or '..' in run_id:raise ValueError('Invalid run ID')
    return ROOT/'research/sync/runs'/run_id


def verify_artifacts(run):
    assert json.loads((run/'status.json').read_text())['status']=='completed'
    entries=json.loads((run/'artifacts.json').read_text())['files']
    for entry in entries:
        assert hashlib.sha256((run/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
    return len(entries)


def execute():
    out=Path(os.environ['GOSC_OUTPUT_DIR']);run_dir=Path(os.environ['GOSC_RUN_DIR'])
    if out.resolve()!=(run_dir/'outputs').resolve() or run_dir.parent!=ROOT/'research/sync/runs':raise ValueError('Invalid run area')
    plan=json.loads(PLAN.read_text());jobs=expand_plan(plan)
    check_frozen(plan,json.loads((ROOT/'results/rev_validation.json').read_text()))
    overlaps=check_ledger(run_dir.parent,run_dir.name,plan)
    limits=resource_limits()
    if int(limits['cpu_quota'])/int(limits['cpu_period'])<2 or int(limits['memory_bytes'])<25769803776:
        raise ValueError('Resource allocation below the approved two-core/24GiB environment')
    source=json.loads((ROOT/'.local/hpc-sync/latest_manifest.json').read_text())
    if source['head']!=BASE_HEAD:raise ValueError('Unexpected baseline')
    for entry in source['files']:
        if hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()!=entry['remote_sha256']:
            raise ValueError('Source changed after sync: '+entry['path'])
    before=snapshot();python=copy_environment(out)
    write_json(out/'plan_snapshot.json',plan);write_json(out/'jobs.json',jobs)
    write_json(out/'execution_context.json',{'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'source_sync_id':source['sync_id'],'baseline_head':BASE_HEAD,'workers':2,'worker_threads':1,
        'campaign_budget_seconds':1860,'per_episode_timeout_seconds':120,'previous_overlaps':overlaps,
        'resource_limits':limits,'seed_role':'Known author frozen validation seeds; no parameter selection or training',
        'cost_scope':'Unmodified base run_episode UL symbols and base dl_symbols; no realistic control-cost claim',
        'training_started':False,'optional_genie_included':False})
    stop={'requested':False}
    def interrupted(signum,frame):stop['requested']=True
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,interrupted)
    try:
        result=run_jobs(jobs,out,ROOT/'.local/r4-a1-workers'/run_dir.name,
            lambda job,spec,dest:[python,ROOT/'scripts/r4_pilot.py','_worker','--job',spec,'--output',dest],
            validate_payload,2,120,1860,cancel=lambda:stop['requested'])
        records=result['records'];done=[r for r in records if r['execution_status']=='completed']
        complete=len(records)==1200 and len(done)==1200 and {r['job_id'] for r in records}=={j['job_id'] for j in jobs}
        counts={s:sum(r['execution_status']==s for r in records) for s in ['completed','failed','timeout','interrupted']}
        value={'status':'complete' if complete else 'partial_or_failed','execution_counts':counts,
            'planned_missions':1200,'terminal_records':len(records),'campaign_wall_seconds':result['elapsed_seconds'],
            'max_active_workers':result['max_active_workers'],'stop_reason':result['stop_reason'],
            'worker_cpu_seconds_completed_processes':math.fsum(r['output']['worker_resources']['cpu_user_seconds']+r['output']['worker_resources']['cpu_system_seconds'] for r in done),
            'max_single_worker_rss_kib':max((r['output']['worker_resources']['max_rss_kib'] for r in done),default=0),
            'gpu_workload':False,'peak_gpu_memory':None,'analysis_status':'separate registered analysis required'}
        write_json(out/'execution_summary.json',value);print(json.dumps(value),flush=True)
    finally:
        after=snapshot();write_json(out/'input_integrity.json',{'before':before,'after':after,'unchanged':before==after})
        if before!=after:raise ValueError('Protected inputs changed')
    return 0 if complete else 1


def paired_statistics(g,p,gy,py):
    import numpy as np
    vectors=[np.asarray(v,dtype=float) for v in (g,p,gy,py)]
    g,p,gy,py=vectors;n=len(g)
    if n<2 or any(v.shape!=(n,) or not np.isfinite(v).all() for v in vectors):raise ValueError('Unequal or invalid paired vectors')
    idx=np.random.default_rng(0).integers(0,n,(4000,n))
    diff=(g-p)[idx].mean(axis=1)
    denominators=gy[idx].mean(axis=1);valid=denominators>0
    ratios=py[idx].mean(axis=1)[valid]/denominators[valid]
    return {'n':n,'outcome_difference_gosc_minus_periodic':[float((g-p).mean()),*map(float,np.percentile(diff,[2.5,97.5]))],
        'uplink_ratio_periodic_over_gosc':([float(py.mean()/gy.mean()),*map(float,np.percentile(ratios,[2.5,97.5]))] if gy.mean()>0 and len(ratios) else None),
        'ratio_valid_resamples':int(valid.sum()),'ratio_invalid_resamples':int((~valid).sum()),
        'bootstrap_resamples':4000,'analysis_seed':0,'interval':'95% pointwise paired percentile bootstrap, not familywise adjusted'}


def analyze(campaign_id):
    import numpy as np
    run=run_path(campaign_id);verify_artifacts(run);source=run/'outputs';out=Path(os.environ['GOSC_OUTPUT_DIR'])
    plan=json.loads((source/'plan_snapshot.json').read_text());expand_plan(plan)
    rows=load_rows(source);assert len(rows)==1200 and all(r['execution_status']=='completed' for r in rows)
    frozen=json.loads((ROOT/'results/rev_validation.json').read_text());check_frozen(plan,frozen)
    groups=[];comparisons=[];historical=[];mismatches=[]
    for scene in plan['settings']:
        setting=scene['name'];metric=frozen[setting]['metric'];target=frozen[setting]['target'];indexed={}
        for arm in scene['arms']:
            scheme=arm['scheme'];selected=[r for r in rows if r['setting']==setting and r['scheme']==scheme]
            indexed[scheme]={r['seed']:r for r in selected}
            assert len(selected)==100 and set(indexed[scheme])==set(range(3000,3100))
            results=[indexed[scheme][seed]['output']['result'] for seed in range(3000,3100)]
            outcomes=np.array([r[metric] for r in results],float);symbols=np.array([r['symbols'] for r in results],float)
            mean=float(outcomes.mean());mean_ul=float(symbols.mean());meets=mean<=target if metric=='completion_time' else mean>=target
            groups.append({'setting':setting,'scheme':scheme,'point':arm['point'],'n':100,'metric':metric,
                'mean_outcome':mean,'author_style_outcome_95ci_halfwidth':float(1.96*outcomes.std(ddof=1)/10),
                'outcome_quantiles':dict(zip(['p05','median','p95'],map(float,np.percentile(outcomes,[5,50,95])))),
                'mean_uplink_symbols':mean_ul,'author_style_ul_95ci_halfwidth':float(1.96*symbols.std(ddof=1)/10),
                'frozen_target':target,'mean_meets_frozen_target':bool(meets),
                'target_margin_positive_is_good':float(target-mean if metric=='completion_time' else mean-target),
                'located_complete_missions':sum(r['completed'] for r in results),
                'fully_saved_missions':sum(r.get('saved',-1)==8 for r in results) if metric=='saved_fraction' else None,
                'mean_found':float(np.mean([r['found'] for r in results])),
                'mean_false_declarations':float(np.mean([r['false_declarations'] for r in results])),
                'mean_bits':float(np.mean([r['bits'] for r in results])),
                'mean_dl_symbols_base_model':float(np.mean([r['dl_symbols'] for r in results]))})
            ref=frozen[setting]['gosc' if scheme=='gosc' else 'periodic'];matched=0
            for i,seed in enumerate(range(3000,3100)):
                ok=outcomes[i]==ref['metric_per_seed'][i] and math.isclose(symbols[i]/1000,ref['ksym_per_seed'][i],abs_tol=1e-10,rel_tol=1e-12)
                if ok:matched+=1
                else:mismatches.append({'setting':setting,'scheme':scheme,'seed':seed,'actual_outcome':float(outcomes[i]),
                    'reference_outcome':ref['metric_per_seed'][i],'actual_symbols':float(symbols[i]),'reference_ksym':ref['ksym_per_seed'][i]})
            historical.append({'setting':setting,'scheme':scheme,'matched_seed_records':matched,'checked_seed_records':100})
        periodic=scene['arms'][1]['scheme'];g=indexed['gosc'];p=indexed[periodic]
        for seed in range(3000,3100):assert g[seed]['output']['world_start_sha256']==p[seed]['output']['world_start_sha256']
        stats=paired_statistics([g[s]['output']['result'][metric] for s in range(3000,3100)],
            [p[s]['output']['result'][metric] for s in range(3000,3100)],
            [g[s]['output']['result']['symbols'] for s in range(3000,3100)],
            [p[s]['output']['result']['symbols'] for s in range(3000,3100)])
        comparisons.append({'setting':setting,'metric':metric,'frozen_target':target,**stats})
    value={'status':'analyzed','campaign_run':campaign_id,'missions':1200,'complete_pairs':600,'groups':groups,
        'paired_comparisons':comparisons,'historical_reproduction':{'all_1200_records_match':not mismatches,
            'groups':historical,'mismatch_count':len(mismatches),'mismatches':mismatches},
        'inference_scope':'Frozen author points on known author seeds; no independent recalibration, no new-method claim. Ratios require task targets/outcomes alongside costs.',
        'unrun':['optional Genie','B','C','calibration','LLM','training']}
    write_json(out/'a1_analysis.json',value)
    with (out/'group_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        fields=[k for k in groups[0] if k!='outcome_quantiles'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(groups)
    with (out/'mission_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['job_id','setting','scheme','seed','process_elapsed_seconds','completion_time','completed','found','saved','saved_fraction','false_declarations','bits','symbols','dl_symbols']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:r.get(k,r['output']['result'].get(k,'')) for k in fields})
    print(json.dumps({'status':'analyzed','missions':1200,'complete_pairs':600,'historical_mismatch_count':len(mismatches),'paired_comparisons':comparisons}),flush=True)
    return 0


def audit(campaign_id,analysis_id):
    run=run_path(campaign_id);analysis=run_path(analysis_id);verify_artifacts(run);verify_artifacts(analysis)
    source=run/'outputs';out=Path(os.environ['GOSC_OUTPUT_DIR']);rows=load_rows(source)
    plan=json.loads((source/'plan_snapshot.json').read_text());context=json.loads((source/'execution_context.json').read_text())
    assert context['plan_sha256']==hashlib.sha256(PLAN.read_bytes()).hexdigest()
    expected={j['job_id']:j for j in expand_plan(plan)};assert len(rows)==1200
    for r in rows:
        j=expected.pop(r['job_id']);assert (r['setting'],r['seed'],r['scheme'],r['config'])==(j['setting'],j['seed'],j['scheme'],j['config'])
        assert r['execution_status']=='completed' and r['process_exit_code']==0
        validate_payload(j,r['output']);assert r['output']['worker_resources']['numeric_library_threads']==1
    assert not expected
    for setting,seed in {(r['setting'],r['seed']) for r in rows}:
        pair=[r for r in rows if r['setting']==setting and r['seed']==seed]
        assert len(pair)==2 and len({r['output']['world_start_sha256'] for r in pair})==1
    active=set();starts=0;ends=0;maximum=0
    for line in (source/'events.jsonl').read_text().splitlines():
        e=json.loads(line);key=e['job_id']
        if e['event']=='start':
            assert key not in active;active.add(key);starts+=1;maximum=max(maximum,len(active));assert len(active)<=2
        else:assert key in active;active.remove(key);ends+=1
    assert starts==ends==1200 and not active
    integrity=json.loads((source/'input_integrity.json').read_text());assert integrity['before']==integrity['after'] and integrity['unchanged']
    for rel,digest in integrity['before'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest
    report=json.loads((analysis/'outputs/a1_analysis.json').read_text());frozen=json.loads((ROOT/'results/rev_validation.json').read_text())
    check_frozen(plan,frozen);historical_matches=0
    for group in report['groups']:
        selected=sorted([r for r in rows if r['setting']==group['setting'] and r['scheme']==group['scheme']],key=lambda r:r['seed'])
        results=[r['output']['result'] for r in selected];n=len(results);assert n==100
        for metric,key in [(group['metric'],'mean_outcome'),('symbols','mean_uplink_symbols'),('bits','mean_bits'),('dl_symbols','mean_dl_symbols_base_model'),('found','mean_found'),('false_declarations','mean_false_declarations')]:
            assert math.isclose(math.fsum(r[metric] for r in results)/n,group[key],rel_tol=1e-12,abs_tol=1e-12)
        ref=frozen[group['setting']]['gosc' if group['scheme']=='gosc' else 'periodic']
        historical_matches+=sum(r[group['metric']]==ref['metric_per_seed'][i] and math.isclose(r['symbols']/1000,ref['ksym_per_seed'][i],abs_tol=1e-10,rel_tol=1e-12) for i,r in enumerate(results))
    # Recompute paired intervals using separately assembled/sorted raw vectors.
    import numpy as np
    for pair in report['paired_comparisons']:
        selected=[r for r in rows if r['setting']==pair['setting']]
        g=sorted([r for r in selected if r['scheme']=='gosc'],key=lambda r:r['seed'])
        p=sorted([r for r in selected if r['scheme']!='gosc'],key=lambda r:r['seed'])
        delta=np.array([a['output']['result'][pair['metric']]-b['output']['result'][pair['metric']] for a,b in zip(g,p)],float)
        gu=np.array([r['output']['result']['symbols'] for r in g],float);pu=np.array([r['output']['result']['symbols'] for r in p],float)
        indices=np.random.default_rng(0).integers(0,100,(4000,100))
        assert np.allclose([delta.mean(),*np.percentile(delta[indices].mean(1),[2.5,97.5])],pair['outcome_difference_gosc_minus_periodic'],rtol=1e-12,atol=1e-12)
        denom=gu[indices].mean(1);valid=denom>0
        rat=pu[indices].mean(1)[valid]/denom[valid]
        assert np.allclose([pu.mean()/gu.mean(),*np.percentile(rat,[2.5,97.5])],pair['uplink_ratio_periodic_over_gosc'],rtol=1e-12,atol=1e-12)
    assert historical_matches==sum(g['matched_seed_records'] for g in report['historical_reproduction']['groups'])
    csvrows=list(csv.DictReader((analysis/'outputs/mission_metrics.csv').open()))
    assert len(csvrows)==1200 and {r['job_id'] for r in csvrows}=={r['job_id'] for r in rows}
    value={'status':'verified','campaign_run':campaign_id,'analysis_run':analysis_id,'unique_missions':1200,
        'complete_pairs':600,'worker_starts':starts,'worker_terminals':ends,'max_concurrency':maximum,
        'frozen_configs_match':True,'protected_inputs_unchanged':True,'groups_and_paired_intervals_verified':True,
        'historical_matched_records':historical_matches,'historical_mismatched_records':1200-historical_matches,
        'new_simulations_in_audit':0,'training_started':False}
    write_json(out/'a1_audit.json',value);print(json.dumps(value),flush=True);return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('validate');sub.add_parser('execute')
    p=sub.add_parser('analyze');p.add_argument('--campaign-run',required=True)
    p=sub.add_parser('audit');p.add_argument('--campaign-run',required=True);p.add_argument('--analysis-run',required=True)
    args=parser.parse_args();require_hpc()
    if args.action=='validate':
        plan=json.loads(PLAN.read_text());jobs=expand_plan(plan);check_frozen(plan,json.loads((ROOT/'results/rev_validation.json').read_text()))
        print(json.dumps({'planned_missions':len(jobs),'scientific_missions_started':0}));return 0
    if args.action=='analyze':return analyze(args.campaign_run)
    if args.action=='audit':return audit(args.campaign_run,args.analysis_run)
    return execute()


if __name__=='__main__':raise SystemExit(main())
