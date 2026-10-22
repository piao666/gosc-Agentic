"""Read-only HPC inventory for the proposed R4 protocol; no mission execution."""
import hashlib
import json
import os
from pathlib import Path
import sys

from hpc_runs import ROOT, require_hpc, write_json
from hpc_reproduce import snapshot


def main():
    require_hpc()
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    before = snapshot()
    work = ROOT/'.local/reproduction-workspaces/hpc-r2-20261019'
    # This existing isolated copy has unchanged original modules and inputs.
    sys.path.insert(0, str(work))
    import experiments.validate_headline as headline
    import experiments.run_revision as revision
    import experiments.run_realistic as realistic
    frozen = json.loads((ROOT/'results/rev_validation.json').read_text())
    counts = []
    for setting in headline.SETTINGS:
        candidates = headline.candidates(setting)
        periodic = [(lab,sch,rs) for fam,lab,sch,cfg,rs in candidates if fam=='periodic']
        families = {}
        for label, scheme, rows in periodic:
            seeds = [x['seed'] for x in rows]
            if len(seeds)!=100 or set(seeds)!=set(range(100)):
                raise RuntimeError('Unexpected paired evaluation seed set: '+setting+'/'+label)
            families.setdefault(scheme, []).append(label)
        counts.append({'setting':setting,'stored_periodic_count':len(periodic),
                       'scheme_counts':{key:len(value) for key,value in families.items()},
                       'stored_labels':families,'all_candidates_have_100_distinct_eval_seeds':True,
                       'frozen_periodic_point':frozen[setting]['periodic']['point']})
    jobs = revision.experiments()['rate_aware']
    generated = {}
    for scheme,label,cfg in jobs:
        generated.setdefault(label.split('/')[0], []).append(cfg.sem_interval)
    frozen_valid = all(len(v['gosc']['metric_per_seed'])==100 and len(v['periodic']['metric_per_seed'])==100
                       for v in frozen.values())
    after = snapshot()
    assert before==after
    report = {'status':'inventoried','periodic_candidates_in_stored_headline_inputs':counts,
              'rate_aware_intervals_in_current_generator':generated,
              'realistic_periodic_family_count':len(realistic.PERIODIC),
              'frozen_records_have_100_paired_metrics':frozen_valid,
              'valuation_price_grids':revision.ETAS,
              'paper_claims_periodic_family_count':38,
              'new_missions_run':0,'training_runs':0,
              'note':'Distinguish stored candidate coverage from current generator code; choose protocol explicitly before recomputing.'}
    write_json(out/'r4_preflight.json', report)
    write_json(out/'input_integrity.json',{'before':before,'after':after,'unchanged':True})
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
