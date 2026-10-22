"""Explicit-schema historical comparisons; zero coverage is never a match."""
import gzip
import json
import math
from collections import Counter

METRICS=['completion_time','completed','found','saved','lost','saved_fraction','symbols','bits','delivered_bits',
'dl_symbols','false_declarations','confirm_latency','private_tv','ul_tx','ul_overhead_bits','ul_ctrl_symbols',
'dl_bcast_symbols','dl_ctrl_symbols','total_symbols','llm_decisions','llm_fallbacks','llm_agree',
'gt_gain','dT','dT_se','n_teammate_changes','est']


def equal(a,b):
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        return (math.isnan(a) and math.isnan(b)) or math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
    return a==b


def load(path):
    with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as stream:
        value=[json.loads(line) for line in stream] if '.jsonl' in path.name else json.load(stream)
    return value['rows'] if isinstance(value,dict) and 'rows' in value else value


def schema(name):
    name=name.removesuffix('.gz')
    if name in ['noise.jsonl','overhead.jsonl','shared.jsonl']:
        return ['setting','arm?','H?','scheme','point','seed']
    if name in ['llm_mixed.jsonl','llm_extended.jsonl']:
        return ['team','scheme','seed']
    if name=='rev_genie_ref.json':return ['param','seed']
    if name=='rev_value_fidelity.json':return ['seed','t','agent','kind']
    return ['scheme','param','seed']


def compare_rows(actual,reference,identity):
    def index(rows):
        result={};counts=Counter();missing=[]
        for i,row in enumerate(rows):
            absent=[field for field in identity if not field.endswith('?') and field not in row]
            if absent:missing.append({'row':i,'missing':absent});continue
            key=json.dumps([row.get(field.rstrip('?')) for field in identity],sort_keys=True)
            counts[key]+=1;result[key]=row
        return result,[{'key':k,'count':v} for k,v in counts.items() if v>1],missing
    a,ad,am=index(actual);b,bd,bm=index(reference)
    report={'identity':identity,'actual_records':len(actual),'original_records':len(reference),
            'actual_duplicate_keys':ad,'original_duplicate_keys':bd,'actual_missing_identity':am,'original_missing_identity':bm}
    if ad or bd or am or bm:return report|{'status':'invalid_identity','compared_common_keys':0,'mismatch_records':None}
    common=sorted(set(a)&set(b));changed=[];metric_comparisons=0;keys_without_metrics=[]
    for key in common:
        metrics=[m for m in METRICS if m in b[key]]
        metric_comparisons+=len(metrics)
        if not metrics:keys_without_metrics.append(key)
        fields=[m for m in METRICS if m in b[key] and (m not in a[key] or not equal(a[key][m],b[key][m]))]
        if fields:changed.append({'key':key,'fields':fields,'values':{m:{'actual':a[key].get(m),'original':b[key].get(m)} for m in fields}})
    report.update(compared_common_keys=len(common),actual_unmatched=len(set(a)-set(b)),original_unmatched=len(set(b)-set(a)),
        actual_coverage=len(common)/len(a) if a else None,reference_coverage=len(common)/len(b) if b else None,
        mismatch_records=len(changed),mismatches=changed,scientific_metric_comparisons=metric_comparisons,keys_without_scientific_metrics=keys_without_metrics)
    status='not_compared' if not common or not metric_comparisons else 'scientific_differences_retained' if changed else 'matching_complete_coverage' if set(a)==set(b) else 'matching_partial_coverage'
    return report|{'status':status}


def compare_file(actual_path,reference_path):
    actual=load(actual_path);reference=load(reference_path)
    if isinstance(actual,list) and actual and isinstance(actual[0],dict) and 'seed' in actual[0]:
        report=compare_rows(actual,reference,schema(actual_path.name))
    else:report={'status':'matching' if equal(actual,reference) else 'scientific_differences_retained','scope':'structured full product comparison'}
    return {'file':actual_path.name}|report
