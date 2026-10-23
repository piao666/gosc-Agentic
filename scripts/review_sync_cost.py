"""HPC-only observational replay of existing calibration, never a new sample."""
from collections import Counter,defaultdict
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gosc.config import Config
from extensions.paid_receiver_service import ServiceConfig
from extensions.sync_cost_diagnostic import ReviewSimulation


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def distribution(xs):
    return None if not xs else {'N_events':len(xs),'mean':float(np.mean(xs)),
        'p50':float(np.quantile(xs,.5)),'p90':float(np.quantile(xs,.9)),'max':float(max(xs))}


def group_summary(rows):
    ul=defaultdict(Counter);dl=defaultdict(Counter);cpu=defaultdict(Counter);receipts=Counter()
    decisions=[];feedback=[];frames=[]
    for row in rows:
        trace=row['trace'];decisions.extend(row['decisions']);feedback.extend(trace['feedback_delays'])
        for x in trace['ul_attempts']:
            ul[x['category']].update({'attempts':1,'uses':x['uses'],'bytes':x['bytes'],'good':int(x['good'])})
            if x['kind']=='summary' and x['unobserved_summary_feedback_before']:
                ul[x['category']]['attempts_before_prior_feedback']+=1
        for x in trace['dl_frames']:
            frames.append(x)
            dl[x['kind']].update({'frames':1,'offered_bytes':x['bytes'],'served_uses':x['served'],
                'completed_frames':int(x['completed'] is not None),'censored_frames':int(x['completed'] is None)})
        for k,v in trace['cpu'].items():cpu[k].update(v)
        receipts.update(trace['receipts'])
    reasons=Counter();peer_ages=[];newer_ages=[];native_ages=[]
    value_by_kind=defaultdict(Counter)
    for d in decisions:
        for peer in d['peers']:
            reasons[peer['reason']]+=1
            if peer['age'] is not None:peer_ages.append(peer['age'])
            if peer['changed']:
                newer_ages.append(peer['age']);native_ages.append(peer['native_age'])
        for v in d['values']:
            stat=value_by_kind[v['key'][0]];stat['options']+=1
            stat['exact_changed']+=v['actual']!=v['public']
            stat['material_changed']+=abs(v['actual']-v['public'])>1e-12+1e-9*max(abs(v['actual']),abs(v['public']))
            stat['both_zero']+=v['actual']==0 and v['public']==0
    counts={'valuation_decisions':len(decisions),
        'peer_opportunities':sum(reasons.values()),'peer_reasons':dict(reasons),
        'decisions_with_changed_pose':sum(any(p['changed'] for p in d['peers']) for d in decisions),
        'decisions_with_exact_value_change':sum(d['exact_value_changed'] for d in decisions),
        'decisions_with_material_value_change':sum(d['material_value_changed'] for d in decisions),
        'decisions_with_selection_change':sum(d['selection_changed'] for d in decisions),
        'decisions_with_payload_choice_change':sum(d['payload_choice_changed'] for d in decisions),
        'decisions_with_no_options':sum(not d['values'] for d in decisions),
        'value_options_by_kind':dict(value_by_kind),
        'stored_peer_age_slots':distribution(peer_ages),
        'changed_peer_age_slots':distribution(newer_ages),
        'replaced_native_age_slots':distribution(native_ages)}
    for key in ('decisions_with_changed_pose','decisions_with_material_value_change','decisions_with_selection_change','decisions_with_payload_choice_change'):
        counts[key+'_fraction']=counts[key]/len(decisions) if decisions else None
    summary_feedback=[x for x in feedback if x['kind']=='summary']
    return {'missions':len(rows),'worlds':len({r['seed'] for r in rows}),
        'UL_pooled':dict(ul),'DL_pooled':dict(dl),'CPU_pooled':dict(cpu),'receipts_pooled':dict(receipts),
        'task_ACK_latency_slots':distribution([x['delay'] for x in feedback if x['kind']=='task']),
        'summary_feedback_latency_slots':distribution([x['delay'] for x in summary_feedback]),
        'summary_feedback_later_than_configured_RTO':sum(x['delay']>x['configured_RTO'] for x in summary_feedback),
        'summary_feedback_count':len(summary_feedback),
        'DL_queue_wait_to_first_service_slots':distribution([x['first_service']-x['enqueued'] for x in frames if x['first_service'] is not None]),
        'DL_enqueue_to_completion_slots':distribution([x['completed']-x['enqueued'] for x in frames if x['completed'] is not None]),
        'projection_and_selection':counts}


def analyse(rows,out):
    groups={case:group_summary([r for r in rows if r['case_id']==case]) for case in ('paid_pose','public_tom')}
    differences=[]
    for seed in sorted({r['seed'] for r in rows}):
        a=next(r for r in rows if r['seed']==seed and r['case_id']=='paid_pose')
        b=next(r for r in rows if r['seed']==seed and r['case_id']=='public_tom')
        ac=a['result']['service']['cost'];bc=b['result']['service']['cost']
        direct_ul=sum(x['uses'] for x in a['trace']['ul_attempts'] if x['kind']=='summary')
        direct_dl=sum(x['served'] for x in a['trace']['dl_frames'] if x['kind'] in ('summary_ack','summary_snapshot'))
        task_ul_a=ac['ul_uses']-direct_ul;task_ul_b=bc['ul_uses']
        task_dl_a=ac['dl_uses']-direct_dl;task_dl_b=bc['dl_uses']
        delta=ac['ul_uses']+ac['dl_uses']-bc['ul_uses']-bc['dl_uses']
        assert delta==direct_ul+direct_dl+task_ul_a-task_ul_b+task_dl_a-task_dl_b
        differences.append({'seed':seed,'direct_summary_UL':direct_ul,'direct_summary_DL':direct_dl,
            'task_UL_difference':task_ul_a-task_ul_b,'task_DL_difference':task_dl_a-task_dl_b,
            'total_uses_difference':delta,'completion_time_difference':a['result']['completion_time']-b['result']['completion_time']})
    means={k:float(np.mean([r[k] for r in differences])) for k in differences[0] if k!='seed'}
    summary={'status':'review_completed_original_results_exact','new_independent_N':0,
        'original_worlds_repeated':12,'replay_missions':len(rows),'matched_original_results':len(rows),
        'groups':groups,'paired_cost_accounting_mean':means,'paired_cost_accounting_per_seed':differences,
        'interpretation':'Accounting identity across two different closed-loop paths, not causal attribution. Shadow prestate comparisons identify only immediate value/choice differences, not downstream reward.',
        'No-Go_retained':True,'reserved_test_run':False,'training':False}
    save(out/'summary.json',summary)
    print(json.dumps({'status':summary['status'],'matches':len(rows),'counts':groups['paid_pose']['projection_and_selection'],
                      'accounting_mean':means}),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',type=Path,default=ROOT/'research/protocols/sync_cost_review_v1.json');a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    p=read(a.plan);frozen_path=ROOT/p['original_freeze'];frozen=read(frozen_path)
    for name,expected in frozen['source_sha256'].items():
        if sha(ROOT/name)!=expected:raise RuntimeError('Original source changed: '+name)
    out=Path(os.environ['GOSC_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
    save(out/'preflight.json',{'status':'original_frozen_source_hashes_match','original_freeze_sha256':sha(frozen_path),
        'review_plan_sha256':sha(a.plan),'new_independent_N':0,'sources':frozen['source_sha256']})
    rows=[]
    for seed in p['seeds']:
        for case_id in p['cases']:
            source=ROOT/'research/sync/runs'/p['original_run']/'outputs'/(str(seed)+'-'+case_id+'.json')
            old=read(source);case=old['case'];start=time.monotonic()
            def expired(*_):raise TimeoutError('Diagnostic per mission timeout')
            signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,p['per_mission_timeout_seconds'])
            try:
                cfg=Config(max_steps=frozen['plan']['calibration_steps'],energy_price=case['price'],filter_eps=case['eps'],sem_interval=case['interval'])
                s=ReviewSimulation(cfg,seed,ServiceConfig(**frozen['plan']['service']),case['mode'],case['pose'],frozen['plan']['dl_loss'])
                result=s.run();trace=s.trace.result()
                row={'seed':seed,'case_id':case_id,'original_sha256':sha(source),'result':result,
                     'original_result_exact_match':result==old['result'],'trace':trace,'decisions':s.decisions,
                     'wall_seconds_including_shadow_observation':time.monotonic()-start}
                save(out/(str(seed)+'-'+case_id+'.json'),row)
                if result!=old['result']:raise RuntimeError('Result mismatch; stop interpretation')
                rows.append(row)
                print(json.dumps({'seed':seed,'case':case_id,'matched':True,'seconds':row['wall_seconds_including_shadow_observation']}),flush=True)
            except Exception as e:
                save(out/(str(seed)+'-'+case_id+'-failure.json'),{'error':repr(e),'original':str(source)})
                raise
            finally:signal.setitimer(signal.ITIMER_REAL,0)
    analyse(rows,out)


if __name__=='__main__':main()
