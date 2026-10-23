"""Independent artifact arithmetic/identity audit; no mission execution."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import NormalDist
import numpy as np


def read(p):return json.loads(p.read_text())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--frozen',type=Path,required=True)
    ap.add_argument('--probe',type=Path,required=True);ap.add_argument('--calibration',type=Path)
    a=ap.parse_args()
    if os.getuid()!=8301880:raise RuntimeError('HPC only')
    p=read(a.frozen);plan=p['plan'];cases=[c['id'] for c in p['cases']]
    checked=[];descriptive=[];rows=read(a.probe/'results.json');assert len(rows)==24
    for phase,seeds,rr in [('probe',plan['probe_seeds'],rows)]+([] if a.calibration is None else [('calibration',plan['calibration_seeds'],read(a.calibration/'results.json'))]):
        assert {(r['seed'],r['case_id']) for r in rr}=={(s,c) for s in seeds for c in cases}
        assert len(rr)==len(seeds)*len(cases)
        for r in rr:
            assert r['status']=='completed' and r['result']['world_sha256']==p['worlds'][str(r['seed'])]
            assert all(v>=0 for v in r['result']['service']['cost'].values())
            assert len(r['result']['curve'])== (24 if phase=='probe' else 400)
        for seed in seeds:
            hashes=[r['result']['event_field_hashes'] for r in rr if r['seed']==seed]
            assert all(x==hashes[0] for x in hashes)
        checked.append({'phase':phase,'missions':len(rr),'worlds':len(seeds)})
        for case in cases:
            group=[r for r in rr if r['case_id']==case]
            descriptive.append({'phase':phase,'case':case,
                'mean_UL':float(np.mean([r['result']['service']['cost']['ul_uses'] for r in group])),
                'mean_DL':float(np.mean([r['result']['service']['cost']['dl_uses'] for r in group])),
                'mean_summary_UL_bytes':float(np.mean([r['result']['service']['cost']['ul_summary_bytes'] for r in group])),
                'mean_pending_DL_frames':float(np.mean([r['result']['service']['pending_dl_frames'] for r in group])),
                'mean_final_pose_cache_items':float(np.mean([sum(r['final_cache_sizes'].values()) for r in group]))})
    budget=read(a.probe/'budget.json')
    projection=2*sum(max(r['wall_seconds'] for r in rows if r['case_id']==c) for c in cases)*400/24*12
    assert math.isclose(projection,budget['projected_calibration_seconds_with_2x_margin'])
    if a.calibration:
        rr=read(a.calibration/'results.json');d=read(a.calibration/'decision.json')
        means={c:np.mean([r['result']['completion_time'] for r in rr if r['case_id']==c]) for c in cases}
        def costs(c):return np.array([r['result']['service']['cost']['ul_uses']+r['result']['service']['cost']['dl_uses'] for r in sorted(rr,key=lambda r:r['seed']) if r['case_id']==c])
        selected=min(cases[:10],key=lambda c:(means[c],costs(c).mean(),c))
        assert selected==d['selected_M0star']
        for comparison in d['comparisons']:
            c=comparison['comparator']
            assert math.isclose(means[c]-means['paid_pose'],comparison['mean_gain_slots'],abs_tol=1e-10)
            assert math.isclose(costs('paid_pose').mean()/costs(c).mean(),comparison['mean_cost_ratio'])
            z=NormalDist().inv_cdf(.9875)+NormalDist().inv_cdf(.95)
            assert comparison['N_task']==math.ceil((z*comparison['gain_SD_planning_upper']/3)**2)
            assert comparison['N_cost']==math.ceil((z*comparison['log_ratio_influence_SD_planning_upper']/math.log(1.05))**2)
        assert d['candidate_test_N']==max([40]+[x[k] for x in d['comparisons'] for k in ('N_task','N_cost')])
        if d['candidate_test_N']>200:assert d['status']=='No-Go' and d['executable_test_N'] is None
        assert d['test_run'] is False and d['training']=='No-Go'
    result={'status':'passed','checks':checked,'descriptive_service_ledger':descriptive,'seed_conflicts':p['seed_conflicts'],
            'unique_frozen_world_hashes':len(set(p['worlds'].values())),
            'test_simulations_run':0,'scope':'Independent artifact arithmetic, pairing fields and gates; not replication by another researcher or physical deployment validation'}
    out=Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json'
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
