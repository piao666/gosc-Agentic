"""HPC-only acceptance: native noise scope, extra records, printed table comparison."""
import collections
import itertools
import json
import os
from pathlib import Path
import sys
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT))
from hpc_runs import require_hpc,digest
from repro_compare import load
from paper_audit import compare

def save(out,name,x):(out/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR'])
    from experiments.run_realistic import experiments,key,HEADLINE,ARMS
    from experiments.validate_realistic import select,reference
    from experiments.plot_realistic import spearman
    native=experiments()['noise']
    expected={key(dict(r,seed=s)) for r in native for s in range(100)}
    configkeys={k[:-1] for k in expected}
    source=ROOT/'results/noise.jsonl.gz'
    actual=ROOT/'research/sync/runs/resume-radio-noise-20261020/outputs/legacy_results/noise.jsonl'
    original=load(source);fresh=load(actual)
    od={key(r):r for r in original};ad={key(r):r for r in fresh}
    assert len(od)==len(original) and len(ad)==len(fresh)
    extras=[r for r in original if key(r) not in expected]
    missing_expected_reference=expected-set(od)
    missing_expected_actual=expected-set(ad)
    inside=[r for r in original if key(r) in expected]
    groups={}
    with (out/'noise_historical_extras.jsonl').open('x') as f:
        for r in extras:
            f.write(json.dumps(r)+'\n')
            k=(r['setting'],r.get('arm'),r['scheme'],r['point'])
            if k not in groups:groups[k]={'setting':k[0],'arm':k[1],'scheme':k[2],'point':k[3],'seeds':[],
                'classification':'outside_seed_range' if key(r)[:-1] in configkeys else 'outside_native_config_grid'}
            groups[k]['seeds'].append(r['seed'])
    selection=[]
    for st in HEADLINE:
        metric,target=reference(st)
        for arm in ARMS:
            if arm=='exact' and not st.startswith('rescue'):continue
            full=select(original,st,'gosc',metric,target,arm=arm)
            restricted=select(inside,st,'gosc',metric,target,arm=arm)
            selection.append({'setting':st,'arm':arm,'original_all':full,'native_subset':restricted,'unchanged':full==restricted})
    correlation=[]
    for arm in ARMS:
        full=[p for r in original if r.get('arm')==arm and r['setting'] in HEADLINE for p in r.get('value_pairs',[])]
        restricted=[p for r in inside if r.get('arm')==arm and r['setting'] in HEADLINE for p in r.get('value_pairs',[])]
        a=1.0 if arm=='exact' else spearman(full) if full else None
        b=1.0 if arm=='exact' else spearman(restricted) if restricted else None
        correlation.append({'arm':arm,'full_pairs':len(full),'subset_pairs':len(restricted),'paper_code_rho_full':a,
            'paper_code_rho_native_subset':b,'same_printed_2dp':format(a,'.2f')==format(b,'.2f') if a is not None and b is not None else a==b})
    save(out,'noise_scope.json',{'native_configs':len(native),'expected_jobs':len(expected),'reference_records':len(original),
        'actual_records':len(fresh),'extra_reference':len(extras),'missing_expected_reference':len(missing_expected_reference),
        'missing_expected_actual':len(missing_expected_actual),'actual_outside_expected':len(set(ad)-expected),
        'groups':list(groups.values()),'needs_native_grid_supplement':bool(missing_expected_actual),
        'reference_sha256':digest(source),'actual_sha256':digest(actual),
        'definition':'Current public native generator, seeds0-99; extras not silently added to frozen protocol'})
    save(out,'noise_extra_impact.json',{'selection':selection,'correlation':correlation,
        'scope':'Original selection and original spearman implementation; no new simulation'})
    ref=read= json.loads((ROOT/'research/reproduction/paper_table_references.json').read_text())
    figures=ROOT/'research/sync/runs/hpc-live-llm-tables-20261022/outputs/figures'
    results=compare(ref,figures)
    save(out,'paper_tables_current.json',results)
    save(out,'conclusion.json',{'expected_grid_complete':not missing_expected_actual,
        'extra_rows':len(extras),'native_supplement_required':bool(missing_expected_actual),
        'selection_changes_on_removing_extras':sum(not r['unchanged'] for r in selection),
        'rho_2dp_changes_on_removing_extras':sum(not r['same_printed_2dp'] for r in correlation),
        'table_results':[{'table':r['table'],'status':r['status'],'cells':r['cells_checked'],'differences':len(r['differences'])} for r in results],
        'new_simulations':0,'raw_results_modified':False})
if __name__=='__main__':main()
