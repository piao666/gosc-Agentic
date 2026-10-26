"""HPC-only accounting and age/price review of existing GP-v2 artifacts.

No Simulation is instantiated, no task seeds are executed, no policies are
retuned. Selector catalogs below are synthetic numerical diagnostics only.
"""
import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gosc.schemes import Group,Option,lagrangian_select

def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def ack_consumed_lower(attempts,agents,unserved):
    # feedback frame=4+2m bytes; at DLrate2, entries cost8 each,
    # shared header/CRC cost16 per frame, with at most n_agents entries.
    return max(0,8*attempts+16*math.ceil(attempts/agents)-unserved)

def scale_groups(groups,factor):
    if not math.isfinite(factor) or factor<=0:raise ValueError('Positive finite scale required')
    return [replace(g,options=[replace(o,value=o.value*factor) for o in g.options]) for g in groups]

def signature(groups,chosen):
    positions={id(g):i for i,g in enumerate(groups)}
    return sorted((positions[id(g)],g.options.index(o)) for g,o in chosen)

def selector_diagnostic(p):
    rng=np.random.default_rng(p['selector_diagnostic_seed']);counts=Counter();mismatches=[]
    for catalog in range(p['selector_random_catalogs']):
        groups=[]
        for k in range(int(rng.integers(3,7))):
            options=[]
            for j in range(int(rng.integers(2,6))):
                uses=int(rng.integers(5,101));value=int(rng.integers(0,1001))*1e-5
                options.append(Option(1.,uses,uses,value,j))
            groups.append(Group('SYNTHETIC',options,cell=k))
        for factor in p['selector_factors']:
            scaled=scale_groups(groups,factor)
            for price in p['selector_prices']:
                left=signature(scaled,lagrangian_select(scaled,p['selector_budget'],price))
                right=signature(groups,lagrangian_select(groups,p['selector_budget'],price/factor))
                label=str(price);counts[label+'_comparisons']+=1
                if left!=right:
                    counts[label+'_mismatches']+=1
                    mismatches.append(dict(catalog=catalog,factor=factor,price=price,scaled_choice=left,dynamic_price_choice=right,
                                           groups=[dict(cell=g.cell,options=[dict(symbols=o.symbols,value=o.value) for o in g.options]) for g in groups]))
    return dict(status='diagnostic_completed',catalogs=p['selector_random_catalogs'],
                comparisons=sum(v for k,v in counts.items() if k.endswith('_comparisons')),
                counts=dict(counts),mismatches=mismatches,
                scope='Synthetic finite-precision selector checks, not mission replay or proof of universal trajectory equivalence')

def review(p,out,config):
    frozen_path=ROOT/p['frozen'];folder=ROOT/p['calibration'];f=read(frozen_path);plan=f['plan']
    for name,sha in f['source_sha256'].items():assert digest(ROOT/name)==sha,name
    rows=read(folder/'results.json');assert len(rows)==252
    rate=plan['service'].get('ul_rate',1.);dl_rate=plan['service'].get('dl_rate',2.)
    assert rate==1. and dl_rate==2.
    per=[];streams_by_case={};total_events=0;input_hashes={}
    for row in rows:
        key=row['case_id'];seed=row['seed'];result=row['result'];c=result['service']['cost']
        assert result['world_sha256']==f['worlds'][str(seed)]
        agents=len(result['event_field_hashes']);assert agents==6
        path=folder/f'{seed}-{key}-events.jsonl';input_hashes[path.relative_to(ROOT).as_posix()]=digest(path)
        counts=Counter();seconds=Counter();ul=dl=0;replay_bytes=0;task_attempts=[];replays=[];task_cpu=[]
        with path.open() as log:
            for line in log:
                e=json.loads(line);total_events+=1
                if e['stream']=='resource':
                    if e['kind']=='ul':ul+=e['ul_uses']
                    else:dl+=e['uses']
                elif e['stream']=='cpu':
                    counts[e['action']]+=1;seconds[e['action']]+=e['seconds']
                    if e['action']=='task_ready':task_cpu.append(e)
                elif e['stream']=='replay_offer':replay_bytes+=e['bytes'];replays.append(e)
                elif e['stream']=='task_attempt':task_attempts.append(e)
        assert ul==c['ul_uses'] and dl==c['dl_uses']
        assert math.isclose(sum(seconds.values()),c['cpu_seconds'])
        assert c['ul_summary_bytes']%6==0
        attempts=int(c['ul_summary_bytes']//6);summary_ul=48*attempts
        assert summary_ul<=ul
        unserved=4*c['dl_offered_bytes']-dl;assert unserved>=0
        ack_lower=ack_consumed_lower(attempts,agents,unserved)
        replay_offered=4*replay_bytes
        replay_lower=max(0,replay_offered-unserved);replay_upper=min(replay_offered,dl)
        # A new task has >=19 wire bytes (GP CONF/INTENT9 + envelope10),
        # and its first successful UL always offers a10-byte ACK. At DLrate2
        # this is >=116 uses per distinct edge task, separate from replay.
        task_lower=max(0,116*row['edge_tasks']+replay_offered-unserved)
        summary_dl_upper=dl-task_lower
        if row['case']['arm']=='public':
            assert attempts==counts['pose_ready']==0
            summary_dl_upper=0  # No summary input/edge: code proves exact zero.
        assert 0<=ack_lower<=summary_dl_upper<=dl
        derived=dict(seed=seed,case_id=key,arm=row['case']['arm'],price=row['case']['price'],
          completion_time=result['completion_time'],comm=ul+dl,ul=ul,dl=dl,
          summary_attempts=attempts,summary_generated_encoding_jobs=counts['pose_ready'],
          generated_reservations_without_UL_attempt_lower=max(0,counts['pose_ready']-attempts),
          summary_UL_exact=summary_ul,task_UL_exact=ul-summary_ul,
          summary_ACK_consumed_lower=ack_lower,summary_DL_consumed_lower=ack_lower,
          summary_DL_consumed_upper=summary_dl_upper,
          direct_summary_consumed_lower=summary_ul+ack_lower,direct_summary_consumed_upper=summary_ul+summary_dl_upper,
          unserved_DL_uses=unserved,replay_offered_uses=replay_offered,
          replay_consumed_lower=replay_lower,replay_consumed_upper=replay_upper,
          cpu_reserved_seconds=c['cpu_seconds'],cpu_action_counts=dict(counts),cpu_action_reserved_seconds=dict(seconds),
          summary_encoding_reserved_seconds=seconds['pose_ready'],
          valuation_reserved_seconds=seconds['valuation'],
          received_decode_reserved_seconds_unclassified=seconds['received'],
          measured_mission_process_seconds=row['cpu_seconds'],measured_selection_process_seconds=result['selection_process_seconds'])
        per.append(derived);streams_by_case[seed,key]=(task_attempts,replays,task_cpu)
    assert total_events==950281
    ids=sorted({r['case_id'] for r in rows});summaries=[]
    numeric=('completion_time','comm','ul','dl','summary_attempts','summary_generated_encoding_jobs','generated_reservations_without_UL_attempt_lower','summary_UL_exact','task_UL_exact',
             'summary_DL_consumed_lower','summary_DL_consumed_upper','direct_summary_consumed_lower','direct_summary_consumed_upper',
             'unserved_DL_uses','replay_offered_uses','replay_consumed_lower','replay_consumed_upper','cpu_reserved_seconds',
             'summary_encoding_reserved_seconds','valuation_reserved_seconds','received_decode_reserved_seconds_unclassified',
             'measured_mission_process_seconds','measured_selection_process_seconds')
    for key in ids:
        rr=[r for r in per if r['case_id']==key];assert len(rr)==12
        aggregate=dict(case_id=key,N=12,**{k:float(np.mean([r[k] for r in rr])) for k in numeric})
        aggregate['summary_UL_fraction']=aggregate['summary_UL_exact']/aggregate['comm']
        aggregate['direct_summary_fraction_lower']=aggregate['direct_summary_consumed_lower']/aggregate['comm']
        aggregate['direct_summary_fraction_upper']=aggregate['direct_summary_consumed_upper']/aggregate['comm']
        summaries.append(aggregate)
    by={(r['seed'],r['case_id']):r for r in rows};account={r['case_id']:r for r in summaries}
    controls=[]
    for seed in plan['calibration_seeds']:
        a=by[seed,'ignore_p1e-05'];b=by[seed,'public_p1e-05'];sa=streams_by_case[seed,'ignore_p1e-05'];sb=streams_by_case[seed,'public_p1e-05']
        fields=('completion_time','completed','found','curve','false_declarations','confirm_latency')
        controls.append(dict(seed=seed,result_task_fields_equal=all(a['result'][k]==b['result'][k] for k in fields),
          task_attempt_log_equal=sa[0]==sb[0],replay_offer_log_equal=sa[1]==sb[1],task_encode_log_equal=sa[2]==sb[2],
          task_UL_bytes_equal=a['result']['service']['cost']['ul_task_bytes']==b['result']['service']['cost']['ul_task_bytes'],
          comm_difference=(a['result']['service']['cost']['ul_uses']+a['result']['service']['cost']['dl_uses'])-(b['result']['service']['cost']['ul_uses']+b['result']['service']['cost']['dl_uses']),
          scope='Logged field equality only; payloads/DL frame-kind/full receiver trajectories not recorded'))
    zero=[]
    for seed in plan['calibration_seeds']:
        a=by[seed,'age_p0']['result'];b=by[seed,'public_p0']['result']
        zero.append(dict(seed=seed,age_T=a['completion_time'],public_T=b['completion_time'],same_T=a['completion_time']==b['completion_time'],same_curve=a['curve']==b['curve']))
    pose=account['pose_p0.0001'];sensitivity=[]
    for baseline in ('periodic_k8_eps0.0','public_p0.0001'):
        limit=1.05*account[baseline]['comm'];excess=max(0,pose['comm']-limit)
        sensitivity.append(dict(baseline=baseline,pose='pose_p0.0001',mean_allowed_comm=limit,
          mean_required_saving=excess,required_total_reduction_fraction=excess/pose['comm'],
          summary_UL_exact=pose['summary_UL_exact'],
          ledger_comm_if_summary_UL_charge_deleted=pose['comm']-pose['summary_UL_exact'],
          UL_fee_deletion_alone_meets_upper_cost_limit=pose['comm']-pose['summary_UL_exact']<=limit,
          scope='Fixed-trajectory accounting sensitivity only; deleting charges does not implement a protocol or preserve task dynamics'))
    synthetic=selector_diagnostic(p);save(out/'selector_diagnostic.json',synthetic)
    result=dict(status='completed',original_missions=252,original_independent_worlds=12,new_missions=0,new_independent_N=0,
      events_read=total_events,config_sha256=digest(config),frozen_sha256=digest(frozen_path),results_sha256=digest(folder/'results.json'),
      decision_sha256=digest(folder/'decision.json'),method_source_verified=True,summaries=summaries,per_mission=per,
      paid_ignore_public_logged_comparisons=controls,age_zero_price_logged_comparisons=zero,ledger_fee_sensitivity=sensitivity,
      selector_comparisons=synthetic['comparisons'],selector_mismatches=len(synthetic['mismatches']),
      missing_observations=['DL enqueue/frame kind and wire bytes mapping','CPU received kind','age factor/effective timestamps per valuation','predecision candidate values/selected signatures'],
      unchanged_scientific_decision='No-Go',new_protocol_status='review_candidate_not_executable')
    save(out/'review.json',result);save(out/'input_event_hashes.json',input_hashes)
    print(json.dumps({k:v for k,v in result.items() if k not in ('summaries','per_mission','paid_ignore_public_logged_comparisons','age_zero_price_logged_comparisons','ledger_fee_sensitivity')}))
    print(json.dumps(dict(focus=[r for r in summaries if r['case_id'] in p['focus']],sensitivity=sensitivity,
                          control_equal_counts={k:sum(r[k] for r in controls) for k in ('result_task_fields_equal','task_attempt_log_equal','replay_offer_log_equal','task_encode_log_equal','task_UL_bytes_equal')},
                          age_zero_price_same_curve=sum(r['same_curve'] for r in zero))))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path,default=ROOT/'research/protocols/summary_age_review_v1.json');a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    review(read(a.config),Path(os.environ['GOSC_OUTPUT_DIR']),a.config.resolve())

if __name__=='__main__':main()
