"""Independent arithmetic/identity checks for observational replay artifacts."""
from collections import Counter,defaultdict
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def percentage(n,d):return None if not d else 100*n/d


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--replay',type=Path,required=True)
    ap.add_argument('--prior-replay',type=Path);a=ap.parse_args()
    if os.getuid()!=8301880:raise RuntimeError('HPC only')
    p=read(ROOT/'research/protocols/sync_cost_review_v1.json');summary=read(a.replay/'summary.json')
    rows=[];checks=Counter();stats=defaultdict(Counter);per_world=[]
    for seed in p['seeds']:
        for case in p['cases']:
            row=read(a.replay/(str(seed)+'-'+case+'.json'));rows.append(row)
            oldpath=ROOT/'research/sync/runs'/p['original_run']/'outputs'/(str(seed)+'-'+case+'.json')
            old=read(oldpath)
            assert row['original_sha256']==hashlib.sha256(oldpath.read_bytes()).hexdigest()
            assert row['result']==old['result'] and row['original_result_exact_match'] is True
            checks['exact_original_result_matches']+=1
            trace=row['trace'];cost=row['result']['service']['cost']
            assert sum(u['uses'] for u in trace['ul_attempts'])==cost['ul_uses']
            assert sum(f['served'] for f in trace['dl_frames'])==cost['dl_uses']
            assert sum(f['bytes'] for f in trace['dl_frames'])==cost['dl_offered_bytes']
            assert math.isclose(sum(v['work_seconds'] for v in trace['cpu'].values()),cost['cpu_seconds'],abs_tol=1e-8)
            checks['UL_DL_CPU_ledger_matches']+=1
            for f in trace['dl_frames']:
                assert 0<=f['served']<=f['need']
                if f['first_service'] is not None:assert f['first_service']>=f['enqueued']
                assert (f['completed'] is not None)==(f['served']==f['need'])
            for d in row['decisions']:
                if not any(x['changed'] for x in d['peers']):
                    assert not d['exact_value_changed'] and not d['selection_changed']
                if not d['exact_value_changed']:assert not d['selection_changed']
                assert d['selection_changed']==(d['actual_selection']!=d['public_shadow_selection'])
                checks['decision_invariants']+=1
            s=stats[case];s['agent_slots']+=6*row['result']['service']['slots']
            s['direct_summary_UL']+=sum(u['uses'] for u in trace['ul_attempts'] if u['kind']=='summary')
            s['direct_summary_DL']+=sum(f['served'] for f in trace['dl_frames'] if f['kind'] in ('summary_ack','summary_snapshot'))
            s['UL_total']+=cost['ul_uses'];s['DL_total']+=cost['dl_uses']
            s['task_UL_after_edge_success']+=sum(u['uses'] for u in trace['ul_attempts'] if u['category']=='task_retry_after_edge')
            s['task_UL_all']+=sum(u['uses'] for u in trace['ul_attempts'] if u['kind']=='task')
            s['task_DL_replay']+=sum(f['served'] for f in trace['dl_frames'] if f['kind']=='task_replay')
            s['task_DL_initial']+=sum(f['served'] for f in trace['dl_frames'] if f['kind']=='task_initial')
            s['DL_task_ack']+=sum(f['served'] for f in trace['dl_frames'] if f['kind']=='task_ack')
            s['DL_task_receipts']+=trace['receipts'].get('task',0)
            s['DL_duplicate_task_receipts']+=trace['receipts'].get('task_duplicate',0)
            counts=Counter({k:sum(d[k] for d in row['decisions']) for k in ('exact_value_changed','material_value_changed','selection_changed','payload_choice_changed')})
            counts['valuation_decisions']=len(row['decisions']);counts['changed_pose_decisions']=sum(any(x['changed'] for x in d['peers']) for d in row['decisions'])
            s.update(counts)
            per_world.append({'seed':seed,'case':case,**counts,
                'choice_change_percent':percentage(counts['selection_changed'],counts['valuation_decisions'])})
    headline={}
    for case,stat in stats.items():
        group=summary['groups'][case];count=group['projection_and_selection']
        assert stat['valuation_decisions']==count['valuation_decisions']
        assert stat['selection_changed']==count['decisions_with_selection_change']
        headline[case]={'pooled_totals':dict(stat),
            'changed_pose_decision_percent':percentage(stat['changed_pose_decisions'],stat['valuation_decisions']),
            'material_value_change_decision_percent':percentage(stat['material_value_changed'],stat['valuation_decisions']),
            'selection_change_decision_percent':percentage(stat['selection_changed'],stat['valuation_decisions']),
            'payload_choice_change_decision_percent':percentage(stat['payload_choice_changed'],stat['valuation_decisions']),
            'task_UL_after_edge_success_percent':percentage(stat['task_UL_after_edge_success'],stat['task_UL_all']),
            'task_DL_replay_share_total_DL_percent':percentage(stat['task_DL_replay'],stat['DL_total']),
            'DL_duplicate_task_receipt_percent':percentage(stat['DL_duplicate_task_receipts'],stat['DL_task_receipts']),
            'direct_summary_share_total_resource_percent':percentage(stat['direct_summary_UL']+stat['direct_summary_DL'],stat['UL_total']+stat['DL_total']),
            'task_ACK_latency_slots':group['task_ACK_latency_slots'],
            'summary_feedback_latency_slots':group['summary_feedback_latency_slots'],
            'summary_feedback_later_than_RTO':group['summary_feedback_later_than_configured_RTO'],
            'summary_feedback_count':group['summary_feedback_count'],
            'DL_queue_wait_to_first_service_slots':group['DL_queue_wait_to_first_service_slots'],
            'CPU_pooled':group['CPU_pooled']}
    assert checks['exact_original_result_matches']==24 and summary['new_independent_N']==0 and summary['No-Go_retained'] is True
    cost=summary['paired_cost_accounting_mean']
    if a.prior_replay:
        prior=read(a.prior_replay/'summary.json')
        for case in p['cases']:
            for field in ('UL_pooled','DL_pooled','CPU_pooled','projection_and_selection'):
                assert summary['groups'][case][field]==prior['groups'][case][field]
        assert cost==prior['paired_cost_accounting_mean']
        checks['primary_metrics_equal_prior_observer_version']=1
    derived={'direct_summary_cost_share_of_observed_total_difference_percent':percentage(cost['direct_summary_UL']+cost['direct_summary_DL'],cost['total_uses_difference']),
        'peer_reason_percent':{k:percentage(v,summary['groups']['paid_pose']['projection_and_selection']['peer_opportunities']) for k,v in summary['groups']['paid_pose']['projection_and_selection']['peer_reasons'].items()}}
    out={'status':'passed','checks':dict(checks),'headline':headline,'derived':derived,'per_world_counts':per_world,
         'note':'Event-pooled descriptive rates, not independent task samples or causal reward effects; no protocol repair or new world'}
    path=Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json'
    with path.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({'status':'passed','checks':dict(checks),'headline':headline,'derived':derived}))


if __name__=='__main__':main()
