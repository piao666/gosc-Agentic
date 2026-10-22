"""HPC read-only run/comparison metadata audit for the progress report."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from hpc_runs import ROOT,require_hpc,write_json,now
require_hpc()
out=Path(os.environ['GOSC_OUTPUT_DIR']);inputs={}
def load(rel):
    path=ROOT/rel;inputs[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())
report={'generated_at':now(),'scope':'Existing records only, no new scientific missions','stages':[]}
for name in ['selection','selection-fresh','c-frontier','c-where','c-belief']:
    prefix='research/sync/runs/ordered-'+name+'-20261019/'
    status=load(prefix+'status.json')
    row={'stage':name,'status':status['status'],'exit_code':status['exit_code'],'elapsed_seconds':status.get('elapsed_seconds')}
    if status['status']=='completed':
        audit=load(prefix+'outputs/stage_audit.json')
        assert audit['worker_starts']==audit['worker_terminals']==audit['raw_original_job_results']
        integrity=load(prefix+'outputs/input_integrity.json');assert integrity['unchanged']
        row.update(missions=audit['raw_original_job_results'],protected_inputs_unchanged=True)
        comparison=load(prefix+'outputs/original_comparison.json')
        records=[]
        for file in comparison['files']:
            item={k:v for k,v in file.items() if k!='mismatches'}
            differences=file.get('mismatches',[])
            if 'mismatch_records' in file:assert len(differences)==file['mismatch_records']
            fields=Counter();schemes=Counter();primary=0
            for difference in differences:
                fields.update(difference['fields'])
                key=json.loads(difference['key']);schemes.update([str(key[3])])
                primary+=bool(set(difference['fields'])&{'completion_time','completed','found','saved','lost','saved_fraction','false_declarations'})
            if differences:item.update(field_mismatch_counts=dict(fields),scheme_mismatch_counts=dict(schemes),primary_outcome_mismatch_records=primary)
            if file.get('compared_common_keys')==0:item['interpretation']='No comparable keys: cannot claim historical agreement from this generic comparator'
            records.append(item)
        row['comparisons']=records
    if name=='selection':
        audit=load(prefix+'outputs/selection_audit.json')
        row['dedicated_selection_audit']={**audit,'historical_mismatches':len(audit['historical_mismatches'])}
    report['stages'].append(row)
report['ollama_final_environment']=load('research/sync/runs/hpc-ollama-final-check-20261020/outputs/final_environment.json')
report['parent_queue_status']=load('research/sync/runs/hpc-ordered-queue-20261019/status.json')['status']
report['source_input_sha256']=inputs
write_json(out/'progress_audit.json',report)
print(json.dumps({'stages':report['stages'],'parent_queue_status':report['parent_queue_status']},indent=2))
