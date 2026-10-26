"""Independent accounting/statistical artifact audit for registered GP-v2 runs."""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import NormalDist
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())

def audit(frozen,folder,phase='calibration'):
    f=read(frozen);p=f['plan'];rows=read(folder/'results.json')
    ids=[c['id'] for c in f['cases']];seeds=p['probe_seeds'] if phase=='probe' else p['calibration_seeds']
    assert len(rows)==len(ids)*len(seeds)
    assert {(r['seed'],r['case_id']) for r in rows}=={(s,c) for s in seeds for c in ids}
    for name,sha in f['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    max_replays=0;max_refresh=0;total_events=0
    for r in rows:
        assert read(folder/f'{r["seed"]}-{r["case_id"]}.json')==r
        result=r['result'];ledger=result['service']['cost'];ul=dl=work=valuation=0.;attempts=collections.defaultdict(list);counts=collections.Counter();rates=collections.Counter();perdl=collections.Counter();perul=collections.Counter()
        for line in (folder/f'{r["seed"]}-{r["case_id"]}-events.jsonl').read_text().splitlines():
            e=json.loads(line);total_events+=1
            if e['stream']=='resource':
                if e['kind']=='ul':ul+=e['ul_uses'];perul[e['t'],e['sender']]+=e['ul_uses']
                else:dl+=e['uses'];perdl[e['t']]+=e['uses']
            elif e['stream']=='cpu':
                work+=e['seconds']
                if e['action']=='valuation':valuation+=e['seconds']
                assert e['ready']>=e['t']
            elif e['stream']=='task_attempt':attempts[e['sender'],e['ident']].append(e['t'])
            elif e['stream']=='replay_offer':counts[e['sender'],e['ident']]+=1;rates[e['t']]+=1
        assert ul==ledger['ul_uses'] and dl==ledger['dl_uses']
        assert math.isclose(work,ledger['cpu_seconds']) and math.isclose(valuation,ledger['valuation_cpu_seconds'])
        assert math.isclose(valuation,p['policy']['valuation_seconds']*result['selection_calls'])
        assert max(perul.values(),default=0)<=p['service']['ul_capacity']
        assert max(perdl.values(),default=0)<=p['service']['dl_capacity']
        assert all(all(b-a>=result['service']['retry_floor_slots'] for a,b in zip(ts,ts[1:])) for ts in attempts.values())
        assert max(counts.values(),default=0)<=p['policy']['replay_limit']
        assert max(rates.values(),default=0)<=p['policy']['replay_frames_per_refresh']
        max_replays=max(max_replays,max(counts.values(),default=0));max_refresh=max(max_refresh,max(rates.values(),default=0))
        assert result['world_sha256']==f['worlds'][str(r['seed'])]
        if r['case']['arm']=='public':assert ledger['ul_summary_bytes']==0
    if phase=='probe':
        b=read(folder/'budget.json')
        projection=2*sum(max(r['wall_seconds'] for r in rows if r['case_id']==c) for c in ids)/p['probe_steps']*p['calibration_steps']*len(p['calibration_seeds'])
        assert math.isclose(projection,b['projection_seconds_2x'])
        assert b['status']==('passed' if projection<=p['calibration_projection_gate_seconds'] else 'blocked')
        return dict(status='passed',phase='probe',missions=len(rows),independent_short_probe_worlds=len(seeds),
                    resource_events_checked=total_events,max_replay_offers_per_item=max_replays,
                    max_replay_frames_per_refresh=max_refresh,budget_projection_recomputed=projection,
                    budget_gate=b['status'],calibration_missions_run=0,test_missions_run=0,
                    scope='Probe ledger, CPU reservation, retry spacing, replay counts and budget arithmetic checked independently. No task-effect analysis or calibration variance estimate. Age-window behavior covered by contracts, not reconstructed from raw replay log.')
    d=read(folder/'decision.json')
    def vector(case,key):
        rr=sorted([r for r in rows if r['case_id']==case],key=lambda r:r['seed'])
        if key=='T':return np.array([r['result']['completion_time'] for r in rr],float)
        if key=='comm':return np.array([r['result']['service']['cost']['ul_uses']+r['result']['service']['cost']['dl_uses'] for r in rr],float)
        return np.array([r['result']['service']['cost']['cpu_seconds'] for r in rr],float)
    for group,field in [([c['id'] for c in f['cases'] if c['mode']!='tom'],'selected_M0star'),([c['id'] for c in f['cases'] if c['mode']=='tom' and c['arm']=='public'],'selected_public'),([c['id'] for c in f['cases'] if c['arm']=='pose'],'selected_pose')]:
        assert min(group,key=lambda c:(vector(c,'T').mean(),vector(c,'comm').mean(),c))==d[field]
    idx=np.random.default_rng(p['analysis_seed']).integers(0,len(seeds),(p['bootstrap_resamples'],len(seeds)))
    z=NormalDist().inv_cdf(1-p['alpha']/6)+NormalDist().inv_cdf(p['endpoint_power_target']);required=[]
    for entry in d['comparisons']:
        a=entry['pose'];b=entry['comparator'];gain=vector(b,'T')-vector(a,'T')
        assert math.isclose(float(gain.mean()),entry['mean_gain_slots'],abs_tol=1e-12)
        assert np.allclose(np.quantile(gain[idx].mean(axis=1),[.025,.975]),entry['gain_95CI'])
        sd=max(gain.std(ddof=1),np.quantile(gain[idx].std(axis=1,ddof=1),.95))
        required.append(math.ceil((z*sd/3)**2));assert required[-1]==entry['N_task']
        for key in ('comm','cpu'):
            av=vector(a,key);bv=vector(b,key);ratio=av.mean()/bv.mean()
            assert math.isclose(ratio,entry[key+'_ratio'])
            assert np.allclose(np.quantile(av[idx].mean(axis=1)/bv[idx].mean(axis=1),[.025,.975]),entry[key+'_ratio_95CI'])
            influence=(av-ratio*bv)/bv.mean()/ratio
            sd=max(influence.std(ddof=1),np.quantile(influence[idx].std(axis=1,ddof=1),.95))
            required.append(math.ceil((z*sd/math.log(1.05))**2));assert required[-1]==entry['N_'+key]
    assert d['candidate_test_N']==max(40,*required)
    assert not d['confirmatory_test_run'] and d['test_missions_run']==0 and d['training']=='No-Go'
    if d['reasons']:assert d['status']=='No-Go' and d['executable_test_N'] is None
    return dict(status='passed',missions=len(rows),independent_N=len(seeds),resource_events_checked=total_events,
                max_replay_offers_per_item=max_replays,max_replay_frames_per_refresh=max_refresh,
                statistics_and_N_recomputed=True,decision=d['status'],test_missions=0,
                scope='Independent implementation of ledger/selection/CI/power arithmetic; shared raw source/observations, not an external reviewer or new experimental sample')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--frozen',type=Path,required=True);ap.add_argument('--calibration',type=Path,required=True);ap.add_argument('--phase',choices=['calibration','probe'],default='calibration');a=ap.parse_args()
    if os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC only')
    result=audit(a.frozen,a.calibration,a.phase);out=Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json'
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':main()
