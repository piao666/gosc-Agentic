"""Independent final coverage/job-ledger audit; no simulation."""
import collections
import json
import os
from pathlib import Path
import sys
import re
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import require_hpc,digest
from repro_compare import compare_file

def read(path):return json.loads(path.read_text())
def rows(path):
    with path.open() as stream:
        for line in stream:
            if line.strip():yield json.loads(line)
def save(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

def main():
    require_hpc();out=Path(os.environ['GOSC_OUTPUT_DIR']);runs=ROOT/'research/sync/runs'
    pipeline=read(runs/'hpc-ordered-resume-20261020/outputs/pipeline_status.json')
    runspec=pipeline['skipped_completed']+pipeline['stages']
    jobs=[];comparisons=[];warnings=[];issues=[]
    (out/'comparisons').mkdir()
    for entry in runspec:
        rid=entry['run_id'];p=runs/rid/'outputs'
        if (p/'pool-summary.jsonl').exists():
            for summary in rows(p/'pool-summary.jsonl'):
                n=summary['pool'];jpath=p/('pool-%03d-jobs.jsonl'%n)
                counts=collections.Counter();statuses=collections.Counter();job_pids={};rss=0
                for row in rows(jpath):
                    counts[row['index']]+=1;statuses[row['status']]+=1;job_pids[row['index']]=row['pid']
                    rss=max(rss,row.get('worker_process_max_rss_kib',0))
                starts=collections.Counter();ends=collections.Counter();ev_status=collections.Counter();bad_pid=[]
                timeline=[]
                for event in rows(p/('pool-%03d-events.jsonl'%n)):
                    if event['event']=='start':
                        starts[event['index']]+=1;timeline.append((event['time'],1))
                    else:
                        ends[event['index']]+=1;ev_status[event['status']]+=1;timeline.append((event['time'],-1))
                    if job_pids.get(event['index'])!=event['pid']:bad_pid.append(event['index'])
                occupancy=0;peak=0
                for when,delta in sorted(timeline):
                    occupancy+=delta;peak=max(peak,occupancy)
                expected=set(range(summary['planned']))
                ok=(set(counts)==expected and set(starts)==expected and set(ends)==expected
                    and all(v==1 for v in counts.values()) and all(v==1 for v in starts.values())
                    and all(v==1 for v in ends.values()) and not bad_pid and statuses=={'completed':len(expected)}
                    and ev_status=={'completed':len(expected)} and summary['completed']==len(expected)
                    and summary['normal_exit'] and peak<=2 and occupancy==0)
                row={'run_id':rid,'pool':n,'expected':len(expected),'results':sum(counts.values()),
                  'starts':sum(starts.values()),'terminals':sum(ends.values()),'peak_concurrency':peak,
                  'status_counts':dict(statuses),'ledger_verified':ok,'worker_max_rss_kib':rss}
                jobs.append(row)
                if not ok:issues.append(row)
        old=read(p/'original_comparison.json') if (p/'original_comparison.json').exists() else {}
        full=[]
        for original in old.get('files',[]):
            name=original['file'];actual=p/'legacy_results'/name;reference=ROOT/'results'/name
            if not reference.exists() and reference.with_name(reference.name+'.gz').exists():
                reference=reference.with_name(reference.name+'.gz')
            if not actual.exists():
                warnings.append({'run_id':rid,'file':name,'reason':'actual_legacy_result_missing_for_recomparison'})
                continue
            if reference.exists():
                current=compare_file(actual,reference)
            else:
                current={'file':name,'status':'no_original_file_for_this_derived_product'}
            if (original.get('compared_common_keys')==0 and str(original.get('status','')).startswith('matching')):
                warnings.append({'run_id':rid,'file':name,'reason':'old_zero_coverage_success_label_superseded','old_status':original['status'],'new_status':current['status']})
            current['run_id']=rid;full.append(current)
            compact={k:v for k,v in current.items() if k not in ['mismatches','keys_without_scientific_metrics']}
            compact['mismatch_fields']=dict(collections.Counter(field for m in current.get('mismatches',[]) for field in m.get('fields',[])))
            comparisons.append(compact)
        save(out/'comparisons'/(rid+'.json'),full)
    save(out/'job_ledger_audit.json',{'status':'verified' if not issues else 'failed','pools':jobs,
      'total_job_records':sum(r['results'] for r in jobs),'issues':issues,
      'scope':'Independent raw job and worker-event indexes, status, PID, concurrency; simulation jobs and diagnostic jobs are not all missions'})
    save(out/'recomputed_comparison_inventory.json',comparisons)
    save(out/'legacy_comparison_warnings.json',warnings)
    # Record fresh selection exact catalogs / target flags; no new statistics or repicking.
    selection={}
    for rid in ['ordered-selection-20261019','ordered-selection-fresh-20261019','resume-sensitivity-20261020','resume-sensitivity-fresh-20261020','resume-genie-fresh-20261020']:
        p=runs/rid/'outputs';d={}
        if (p/'candidate_configs.json').exists():d['cases']=len(read(p/'candidate_configs.json'))
        if (p/'selection_audit.json').exists():
            raw=read(p/'selection_audit.json')
            d['selection_audit']={k:(len(v) if isinstance(v,list) and k=='historical_mismatches' else v) for k,v in raw.items()}
        if (p/'fresh_validation.json').exists():
            raw=read(p/'fresh_validation.json')
            d['fresh_targets']=[{'setting':setting,'family':family,'point':v[family].get('point'),'meets_target':v[family].get('meets_target'),'metric':v[family].get('fresh_metric')} for setting,v in raw.items() for family in ['gosc','periodic'] if v.get(family)]
        selection[rid]=d
    save(out/'selection_and_fresh_scope.json',selection)
    figures=runs/'resume-final-replot-20261020/outputs/figures'
    pdfs=[{'path':p.relative_to(figures).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(figures.glob('*.pdf'))]
    tables=[]
    for p in sorted(figures.glob('*.tex')):
        text=p.read_text()
        tables.append({'path':p.name,'lines':len(text.splitlines()),'placeholder_ne_count':len(re.findall(r'\bn/e\b',text)),
            'nan_count':len(re.findall(r'\bnan\b',text,flags=re.I)),'sha256':digest(p)})
    save(out/'figure_table_inventory.json',{'pdfs':pdfs,'tables':tables,'pdf_visual_inspection':'not_performed_by_this_numeric_audit','interpretation':'-- may mean unsupported budget; not automatically an error'})
    # Closed cache snapshot, including prompt-key-only author assets, is checked separately.
    save(out/'conclusion.json',{'job_ledgers_verified':not issues,'comparisons_recomputed':len(comparisons),
       'old_zero_coverage_warnings':sum(w['reason']=='old_zero_coverage_success_label_superseded' for w in warnings),
       'raw_history_rewritten':False,'new_missions':0,'new_http_calls':0,'new_training':False})
    if issues:raise RuntimeError('Raw job ledger failed')
if __name__=='__main__':main()
