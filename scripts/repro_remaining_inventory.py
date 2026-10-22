"""HPC-only remaining-reproduction inventory; no scientific mission is executed."""
from pathlib import Path
import dataclasses
import hashlib
import json
import os
import sys

from hpc_runs import ROOT, require_hpc, write_json
from hpc_reproduce import snapshot


def main():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR']);before=snapshot()
    work=ROOT/'.local/reproduction-workspaces/hpc-r2-20261019'
    for folder in ['gosc','experiments']:
        for source in (ROOT/folder).rglob('*.py'):
            target=work/source.relative_to(ROOT)
            assert target.is_file() and source.read_bytes()==target.read_bytes()
    sys.path.insert(0,str(work))
    from experiments import run_all,run_revision,run_realistic,run_belief_divergence,validate_headline
    selected=[]
    for name in validate_headline.SETTINGS:
        base,metric,factor=validate_headline.SETTINGS[name]
        candidates=validate_headline.candidates(name)
        for family,label,scheme,cfg,rows in candidates:
            assert len(rows)==100 and {r['seed'] for r in rows}==set(range(100))
            selected.append({'setting':name,'family':family,'point':label,'scheme':scheme,
                'config':json.loads(json.dumps(dataclasses.asdict(cfg))),'metric':metric,
                'original_seed_metrics':[{'seed':r['seed'],'outcome':r[metric],'symbols':r['symbols']} for r in rows]})
        genie=base
        selected.append({'setting':name,'family':'genie_reference','point':'reference','scheme':'genie',
            'config':json.loads(json.dumps(dataclasses.asdict(genie))),'metric':metric,'original_seed_metrics':[]})
    write_json(out/'selection_catalog.json',selected)
    summaries=[]
    for name in validate_headline.SETTINGS:
        rows=[r for r in selected if r['setting']==name]
        summaries.append({'setting':name,'gosc_points':sum(r['family']=='gosc' for r in rows),
            'periodic_points':sum(r['family']=='periodic' for r in rows),'genie_reference_points':1,
            'missions':len(rows)*100})
    revisions=run_revision.experiments()
    counts={'main':{k:len(v)*100 for k,v in run_all.experiments(100).items()},
        'revision':{k:len(v)*100 for k,v in revisions.items()},
        'realistic':{k:len(v)*100 for k,v in run_realistic.experiments().items()},
        'belief_divergence':len(run_belief_divergence.jobs())*100}
    result={'status':'inventoried','scientific_missions_started':0,'selection_settings':summaries,
        'selection_missions':sum(v['missions'] for v in summaries),'raw_campaign_counts_before_cross_phase_deduplication':counts,
        'calibration':{'status':'missing_original_procedure','declared_seeds':[1000,1079],
            'search':'Current HEAD README and all experiments/gosc sources; only declaration and frozen-after-calibration comments found',
            'missing':['executable calibration procedure','historical search space/selection rule','per-seed calibration records'],
            'constraint':'No invented calibration can be labelled faithful original reproduction'},
        'llm':{'cache_replay':'not_started','live':'runtime_not_available_in_prior_read_only_probe'},
        'source_head':'876fc523b113b3b65e19f0b730f1573ccc2ee17f',
        'note':'Selection seeds0-99 are public author selection data, distinct from calibration1000-1079 and frozen validation3000-3099. No original artifacts overwritten.'}
    after=snapshot();assert before==after
    write_json(out/'remaining_inventory.json',result)
    write_json(out/'input_integrity.json',{'before':before,'after':after,'unchanged':True})
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
