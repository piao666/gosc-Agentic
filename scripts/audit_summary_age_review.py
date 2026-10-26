"""HPC-only independent arithmetic / artifact audit of the summary-age review."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--review',type=Path,required=True);a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    d=read(a.review/'review.json');config=ROOT/'research/protocols/summary_age_review_v1.json';p=read(config)
    folder=ROOT/p['calibration'];rows=read(folder/'results.json');raw={(r['seed'],r['case_id']):r for r in rows}
    assert d['config_sha256']==sha(config) and d['results_sha256']==sha(folder/'results.json')
    assert d['decision_sha256']==sha(folder/'decision.json') and d['frozen_sha256']==sha(ROOT/p['frozen'])
    assert len(d['per_mission'])==len(raw)==252
    for path,digest in read(a.review/'input_event_hashes.json').items():assert sha(ROOT/path)==digest,path
    for row in d['per_mission']:
        r=raw[row['seed'],row['case_id']];c=r['result']['service']['cost'];m=c['ul_summary_bytes']//6
        # Independently parse raw events, rather than trusting the derived
        # replay-byte and CPU-action fields used in the arithmetic below.
        replay_bytes=0;ul=dl=0;pose_jobs=0;cpu={}
        with (folder/f'{row["seed"]}-{row["case_id"]}-events.jsonl').open() as events:
            for line in events:
                e=json.loads(line)
                if e['stream']=='replay_offer':replay_bytes+=e['bytes']
                elif e['stream']=='resource':
                    if e['kind']=='ul':ul+=e['ul_uses']
                    else:dl+=e['uses']
                elif e['stream']=='cpu':
                    cpu.setdefault(e['action'],[]).append(e['seconds'])
                    if e['action']=='pose_ready':pose_jobs+=1
        assert ul==c['ul_uses'] and dl==c['dl_uses']
        assert row['replay_offered_uses']==4*replay_bytes
        assert row['summary_generated_encoding_jobs']==pose_jobs
        for name,values in cpu.items():assert math.isclose(math.fsum(values),row['cpu_action_reserved_seconds'][name])
        for field,action in [('summary_encoding_reserved_seconds','pose_ready'),('valuation_reserved_seconds','valuation'),('received_decode_reserved_seconds_unclassified','received')]:
            assert math.isclose(row[field],math.fsum(cpu.get(action,[])))
        assert c['ul_summary_bytes']==6*m and row['summary_UL_exact']==8*c['ul_summary_bytes']
        assert row['task_UL_exact']==c['ul_uses']-row['summary_UL_exact']
        pending=4*c['dl_offered_bytes']-c['dl_uses']
        ack_lower=max(0,8*m+16*((m+5)//6)-pending)
        assert row['summary_DL_consumed_lower']==ack_lower
        task_lb=max(0,116*r['edge_tasks']+row['replay_offered_uses']-pending)
        upper=0 if r['case']['arm']=='public' else c['dl_uses']-task_lb
        assert row['summary_DL_consumed_upper']==upper
        assert row['generated_reservations_without_UL_attempt_lower']==max(0,row['summary_generated_encoding_jobs']-m)
        assert ack_lower<=row['summary_DL_consumed_upper']
        assert row['direct_summary_consumed_lower']==row['summary_UL_exact']+ack_lower
        assert row['direct_summary_consumed_upper']==row['summary_UL_exact']+row['summary_DL_consumed_upper']
        assert row['replay_consumed_lower']==max(0,row['replay_offered_uses']-pending)
        assert row['replay_consumed_upper']==min(row['replay_offered_uses'],c['dl_uses'])
        assert math.isclose(math.fsum(row['cpu_action_reserved_seconds'].values()),c['cpu_seconds'])
    by={r['case_id']:r for r in d['summaries']}
    for aggregate in d['summaries']:
        rr=[r for r in d['per_mission'] if r['case_id']==aggregate['case_id']]
        assert len(rr)==aggregate['N']==12
        for key,value in aggregate.items():
            if key in rr[0] and isinstance(value,(int,float)):
                assert math.isclose(value,math.fsum(r[key] for r in rr)/12,rel_tol=1e-12,abs_tol=1e-12),key
    for e in d['ledger_fee_sensitivity']:
        pose=by[e['pose']];baseline=by[e['baseline']]
        assert math.isclose(e['mean_allowed_comm'],1.05*baseline['comm'])
        assert math.isclose(e['mean_required_saving'],max(0,pose['comm']-1.05*baseline['comm']))
        assert math.isclose(e['ledger_comm_if_summary_UL_charge_deleted'],pose['comm']-pose['summary_UL_exact'])
    synthetic=read(a.review/'selector_diagnostic.json')
    assert synthetic['comparisons']==p['selector_random_catalogs']*len(p['selector_factors'])*len(p['selector_prices'])==1536
    assert len(synthetic['mismatches'])==d['selector_mismatches']
    assert d['new_missions']==d['new_independent_N']==0 and d['unchanged_scientific_decision']=='No-Go'
    result=dict(status='passed',original_missions=252,event_files_hashed=252,event_files_reparsed=252,new_missions=0,
                bounds_and_fee_sensitivity_recomputed=True,aggregates_recomputed=True,
                selector_diagnostic_comparisons=1536,selector_mismatches=d['selector_mismatches'],
                review_sha256=sha(a.review/'review.json'),scope='Independent arithmetic/hash audit, not external replication or new scientific N')
    with (Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':main()
