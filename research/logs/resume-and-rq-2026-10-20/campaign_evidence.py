"""HPC evidence closure before the remaining original campaign; no new missions."""
from pathlib import Path
import json,os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from hpc_runs import ROOT,require_hpc,write_json,resource_limits
sys.path.insert(0,str(ROOT))
from repro_resume import validate_state
from repro_ordered import WORK

def main():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR']);resume=validate_state(ROOT,WORK)
    from experiments.run_realistic import experiments
    grids={name:len(rows)*100 for name,rows in experiments().items()}
    assert grids=={'noise':23400,'shared':18400,'overhead':82600}
    processes=subprocess.check_output(['ps','-eo','pid,args']).decode()
    lingering=[line for line in processes.splitlines() if 'repro_legacy.py --workspace' in line or 'repro_ordered.py stage --name' in line]
    if lingering:raise RuntimeError('Unexpected scientific workers before continuation: '+repr(lingering))
    science=subprocess.check_output(['git','diff','--name-only','HEAD','--','gosc','experiments','tests','results','LICENSE'],cwd=ROOT).decode().strip()
    if science:raise RuntimeError('Protected source changed: '+science)
    traces=json.loads((ROOT/'research/sync/runs/hpc-c-resume-20261020/outputs/trace_divergence.json').read_text())
    concise=[{**{k:v for k,v in row.items() if k!='first_choice_difference'},'first_choice_difference':None if row['first_choice_difference'] is None else {k:v for k,v in row['first_choice_difference'].items() if k not in ['current_options','variant_options']}} for row in traces]
    write_json(out/'trace_summary.json',concise)
    stats=json.loads((ROOT/'research/sync/runs/resume-c-analysis-20261020/outputs/matched_statistics.json').read_text())['statistics']
    comparisons=[]
    for st,budgets in stats.items():
        for budget,schemes in budgets.items():
            for scheme in ['gosc_bits','gosc_aoi']:
                row=schemes.get(scheme)
                if row:comparisons.append({'setting':st,'budget':budget,'scheme':scheme,**row})
    write_json(out/'c_simple_value_summary.json',{'comparisons':comparisons,'n_comparisons':len(comparisons),'uncorrected_positive':sum(r['lo']>0 for r in comparisons),'bonferroni_positive':sum(r['bonf_lo']>0 for r in comparisons),'meaning':'Positive means original ToM faster than comparator at native interpolated matched cost; not an equivalence test'})
    manifest=json.loads((ROOT/'research/literature/reading_manifest_2026-10-20.json').read_text())
    assert len(manifest['sources'])==13
    for item in manifest['sources']:
        text=(ROOT/item['note']).read_text()
        assert item['pdf_sha256'] in text and 'PAPER' in text and '五句话' in text
    report={'status':'verified','uid':os.getuid(),'resources':resource_limits(),'resume':resume,'realistic_candidate_missions':grids,'realistic_fresh_maximum':10300,'fresh_exact_plan':'Computed before radio-fresh from completed grids, actual config/scheme/seed catalog audited against native jobs','protected_git_paths_unchanged':True,'literature_notes_checked':13,'new_method_training_started':False,'numeric_threads':1}
    write_json(out/'campaign_preflight.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['resume']}));print('Completed original stages:',len(resume['completed_prefix']),'Remaining:',len(resume['pending']))
if __name__=='__main__':main()
