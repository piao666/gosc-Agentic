"""Independent raw-file/ledger/budget/statistical checks for GP-ID-CAL-v1."""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from scripts.audit_information_identifiability import resource_audit, decision_audit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def assert_same(actual, expected):
    if isinstance(expected,dict):
        require(isinstance(actual,dict) and set(actual)==set(expected),'Object field mismatch')
        for key in expected:
            assert_same(actual[key],expected[key])
    elif isinstance(expected,list):
        require(isinstance(actual,list) and len(actual)==len(expected),'List shape mismatch')
        for a,b in zip(actual,expected):assert_same(a,b)
    elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
        require(isinstance(actual,(int,float)) and not isinstance(actual,bool) and
                math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-10),'Numeric mismatch')
    else:
        require(actual==expected,'Value mismatch')


def read_artifact(directory, metadata):
    directory=Path(directory).resolve();path=(directory/metadata['path']).resolve()
    require(directory in path.parents and not path.is_symlink(),'Artifact path')
    require(path.stat().st_size==metadata['compressed_bytes'] and digest(path)==metadata['sha256'],'Compressed SHA/hash mismatch')
    h=hashlib.sha256();count=size=0
    with gzip.open(path,'rb') as stream:
        for line in stream:
            h.update(line);size+=len(line);count+=1
            yield json.loads(line)
    require(count==metadata['rows'] and size==metadata['uncompressed_bytes'],'Decompressed size/count')
    require(h.hexdigest()==metadata['uncompressed_sha256'],'Uncompressed SHA/hash mismatch')


def audit_selector(events, numeric):
    observed=[e for e in events if e['event']=='decision' and e['groups_before_age'] is not None]
    index={(e['t'],e['sender'],e['form']):e for e in observed}
    require(len(index)==len(observed) and len(numeric)==len(observed),'Selector count')
    seen=set();replay=cross=0
    for d in numeric:
        key=(d['t'],d['sender'],d['original_form'])
        require(key in index and key not in seen,'Selector binding')
        seen.add(key)
        require(set(d['selected'])=={'scale','price'},'Selector forms')
        same=d['selected'][key[2]]==index[key]['selected']
        equal=d['selected']['scale']==d['selected']['price']
        require(d['replay_matches_actual']==same and d['scale_price_same']==equal,'Selector claim mismatch')
        replay+=not same;cross+=not equal
    require(seen==set(index) and replay==0,'Selector actual replay')
    return dict(diagnostics=len(numeric),replay_mismatches=replay,cross_form_mismatches=cross)


def recompute_projection(rows,plan):
    seconds=0.;size=0.
    for case in plan['arms']+plan['simple_references']:
        cells=[r for r in rows if r['case_id']==case]
        require(len(cells)==len(plan['budget_seeds']),'Budget case matrix')
        seconds+=max(r['end_to_end_wall_seconds'] for r in cells)
        size+=max(r['artifact_bytes'] for r in cells)
    factor=2*len(plan['calibration_seeds'])*plan['calibration_steps']/plan['budget_steps']
    return dict(projected_seconds=factor*seconds,projected_bytes=factor*size+131072)


def selection_budget_status(findings):
    return 'blocked_selection_budget' if findings else 'passed'


def verify_files(results_path,frozen_path,*,collect_budget_findings=False):
    data=read(results_path);frozen=read(frozen_path);plan=frozen['plan']
    require(data['frozen']==frozen and data['frozen_sha256']==digest(frozen_path),'Frozen input binding')
    require(plan['user_authorized'] and not plan['formal_test_authorized'] and not plan['training'],'Authorization scope')
    require(not data['formal_test_run'] and not data['training'],'Execution scope')
    require(plan['primary_endpoint_family']==3*len(plan['primary_comparisons'])==15,'Statistical family')
    require(plan['primary_method']=='paid-pose' and len(frozen['cases'])==13,'Frozen method/case count')
    phase=data['phase'];require(phase in ('budget','calibration'),'Phase')
    require(data['calibration_run']==(phase=='calibration'),'Phase/calibration flag')
    seeds=plan['budget_seeds'] if phase=='budget' else plan['calibration_seeds']
    steps=plan['budget_steps'] if phase=='budget' else plan['calibration_steps']
    cases={c['id']:c for c in frozen['cases']}
    require(set(cases)==set(plan['arms']+plan['simple_references']),'Case names')
    keys=[(r['seed'],r['case_id']) for r in data['rows']]
    require(len(keys)==len(set(keys)) and set(keys)=={(s,c) for s in seeds for c in cases},'Complete paired matrix')
    reports=[];findings=[];input_hashes={'results.json':digest(results_path)}
    for row in data['rows']:
        seed,case=row['seed'],row['case_id'];result=row['result']
        require(row['status']=='completed' and row['phase']==phase and row['case']==cases[case],'Row identity/status')
        require(result['world_sha256']==frozen['worlds'][str(seed)],'Frozen world identity')
        require(0<=result['completion_time']<=steps and result['completed']==(result['found']==8),'Task horizon/completion')
        require(result['completed'] or result['completion_time']==steps,'Early task truncation')
        require(0<=row['mission_wall_seconds']<=row['end_to_end_wall_seconds']<=plan['per_mission_timeout_seconds'],'Whole-case timing')
        standalone=Path(results_path).parent/(str(seed)+'-'+case+'.json')
        saved=read(standalone)
        for key in ('seed','case_id','case','phase','status','result','observation','selector'):
            assert_same(saved[key],row[key])
        require(saved['end_to_end_wall_seconds']<=row['end_to_end_wall_seconds'],'Standalone timing scope')
        input_hashes[standalone.name]=digest(standalone)
        observation=list(read_artifact(Path(results_path).parent,row['observation']))
        numeric=list(read_artifact(Path(results_path).parent,row['selector']))
        for key in ('observation','selector'):
            input_hashes[row[key]['path']]=row[key]['sha256']
        ledger=resource_audit(observation,result,plan)
        row_findings=[] if collect_budget_findings else None
        count=decision_audit(observation,result,selection_budget_findings=row_findings)
        if row_findings:
            findings.extend(dict(seed=seed,case_id=case,**item) for item in row_findings)
        selected=audit_selector(observation,numeric)
        for key,value in selected.items():require(row['selector'][key]==value,'Selector metadata mismatch')
        actual_artifact_bytes=sum((Path(results_path).parent/row[k]['path']).stat().st_size for k in ('observation','selector'))+standalone.stat().st_size
        require(row['artifact_bytes']>=actual_artifact_bytes,'Artifact byte budget undercounts row files')
        reports.append(dict(seed=seed,case_id=case,decisions=count,selector=selected,ledger=ledger))
    actual_bytes=sum(p.stat().st_size for p in Path(results_path).parent.rglob('*') if p.is_file())
    require(actual_bytes<=plan['compressed_output_cap_bytes'],'Actual campaign output cap')
    return data,dict(status=selection_budget_status(findings),phase=phase,rows=len(data['rows']),actual_output_bytes=actual_bytes,
                     details=reports,input_sha256=input_hashes,frozen_sha256=digest(frozen_path),
                     selection_budget_findings=findings,diagnostic_continuation=collect_budget_findings,
                     audit_source_sha256={name:digest(ROOT/name) for name in
                         ('scripts/audit_information_calibration.py','scripts/audit_information_identifiability.py')})


def _independent_endpoint(value,samples,plan,family):
    invalid=int(np.count_nonzero(~np.isfinite(samples)))
    state='defined';unadjusted=adjusted=None
    if value is None or not math.isfinite(value) or invalid:
        state='undefined'
    else:
        unadjusted=np.quantile(samples,[.025,.975],method='linear').tolist()
        if family:
            q=plan['alpha']/(2*plan['primary_endpoint_family'])
            adjusted=np.quantile(samples,[q,1-q],method='linear').tolist()
        if float(np.max(samples)-np.min(samples))==0:state='degenerate'
    return dict(estimate=value,ci95=unadjusted,ci_family=adjusted,status=state,
                bootstrap_valid=int(samples.size-invalid),bootstrap_undefined=invalid)


def audit_statistics(data,answer):
    """Rebuild all primary/secondary estimates and intervals from task rows."""
    plan=data['frozen']['plan'];seeds=plan['calibration_seeds'];n=len(seeds)
    ids=[c['id'] for c in data['frozen']['cases']]
    index={(r['seed'],r['case_id']):r for r in data['rows']}
    draw=np.random.default_rng(plan['analysis_seed']).integers(0,n,(plan['bootstrap_resamples'],n),dtype=np.int64)
    require(answer['bootstrap_index_sha256']==hashlib.sha256(draw.tobytes()).hexdigest(),'Bootstrap index identity')
    require(answer['N']==12 and answer['missions']==156 and answer['formal_test_N'] is None and not answer['formal_test_run'] and not answer['training'],'Analysis scope/N')
    vector={};summaries=[]
    for case in ids:
        rows=[index[s,case] for s in seeds]
        arrays=dict(time=np.array([r['result']['completion_time'] for r in rows],float),
            comm=np.array([r['result']['service']['cost']['ul_uses']+r['result']['service']['cost']['dl_uses'] for r in rows],float),
            cpu=np.array([r['result']['service']['cost']['cpu_seconds'] for r in rows],float))
        vector[case]=arrays
        summary=dict(id=case,N=n,completed=sum(r['result']['completed'] for r in rows),not_completed=sum(not r['result']['completed'] for r in rows),
            false_declarations=sum(r['result']['false_declarations'] for r in rows),
            mean_mission_wall_seconds=sum(r['mission_wall_seconds'] for r in rows)/n,
            mean_end_to_end_wall_seconds=sum(r['end_to_end_wall_seconds'] for r in rows)/n,
            mean_recording_process_seconds=sum(r['process_seconds'] for r in rows)/n)
        for key,arr in arrays.items():
            summary['mean_'+key]=float(sum(arr)/n)
            quant=np.quantile(arr,[0,.25,.5,.75,.9,1.],method='linear')
            summary[key+'_quantiles']=dict(zip(('min','p25','p50','p75','p90','max'),map(float,quant)))
        summaries.append(summary)
    assert_same(answer['cases'],summaries)
    primary_expected=[]
    for source,dest,family in (('primary_comparisons','primary',True),('secondary_comparisons','secondary',False)):
        expected=[]
        for c in plan[source]:
            t,b=vector[c['treatment']],vector[c['control']]
            gain=b['time']-t['time']
            entry={'gain':_independent_endpoint(float(sum(gain)/n),np.mean(gain[draw],axis=1),plan,family)}
            for key in ('comm','cpu'):
                ratio=float(sum(t[key])/sum(b[key])) if sum(b[key])>0 else None
                with np.errstate(divide='ignore',invalid='ignore'):
                    distribution=np.mean(t[key][draw],axis=1)/np.mean(b[key][draw],axis=1)
                entry[key+'_ratio']=_independent_endpoint(ratio,distribution,plan,family)
            support=all(entry[k]['estimate'] is not None and .95<=entry[k]['estimate']<=1.05 for k in ('comm_ratio','cpu_ratio'))
            ci='ci_family' if family else 'ci95'
            positive=(all(e['status']=='defined' for e in entry.values()) and entry['gain'][ci][0]>=3 and all(entry[k][ci][1]<=1.05 for k in ('comm_ratio','cpu_ratio')))
            expected.append(dict(id=c['id'],treatment=c['treatment'],control=c['control'],**entry,
                mean_joint_cost_support=support,noninferiority_screen=bool(positive),matched_screen=bool(positive and support)))
        assert_same(answer[dest],expected)
        if family:primary_expected=expected
    primary={c['id']:c for c in primary_expected}
    eligible=all(primary[k]['matched_screen'] for k in plan['primary_method_comparison_ids'])
    require(answer['primary_method']=='paid-pose' and answer['primary_method_eligible']==eligible,'Frozen primary decision')
    require(answer['timestamp_screen']==primary['timestamp_use']['matched_screen'],'Timestamp screen')
    require(answer['status']==('eligible_for_future_formal_protocol_review' if eligible else 'No-Go'),'Exploratory decision')
    return dict(statistical_estimates_and_intervals='independently_recomputed',N=n,primary_family_endpoints=15,
                primary_method_eligible=eligible,scientific_status=answer['status'],formal_test_N=None)


def audit_budget(results_path,budget_path,frozen_path):
    data,report=verify_files(results_path,frozen_path);plan=data['frozen']['plan'];budget=read(budget_path)
    require(data['phase']=='budget','Budget phase')
    expected=recompute_projection(data['rows'],plan)
    for key,value in expected.items():assert_same(budget[key],value)
    require(budget['results_sha256']==digest(results_path) and budget['frozen_sha256']==digest(frozen_path),'Budget input SHA binding')
    passed=(expected['projected_seconds']<=plan['calibration_projection_gate_seconds'] and
            expected['projected_bytes']<=plan['compressed_output_cap_bytes'] and budget['free_bytes']>=plan['minimum_free_bytes'])
    require(budget['gate_passed']==passed,'Budget gate decision')
    return {**report,'status':'passed' if passed else 'blocked','budget_sha256':digest(budget_path),
            'results_sha256':digest(results_path),'projected_seconds':expected['projected_seconds'],
            'projected_bytes':expected['projected_bytes']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['budget','calibration'],required=True)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--frozen',type=Path,required=True)
    p.add_argument('--budget',type=Path);p.add_argument('--analysis',type=Path)
    p.add_argument('--collect-budget-findings',action='store_true',
        help='Diagnostic continuation only: record every budget violation; any violation remains blocked')
    a=p.parse_args()
    if os.name!='posix' or os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':raise RuntimeError('HPC-only')
    if not os.environ.get('GOSC_RUN_DIR') or not os.environ.get('GOSC_OUTPUT_DIR'):raise RuntimeError('Registered runner required')
    if a.mode=='budget':
        if a.collect_budget_findings:p.error('Diagnostic continuation is calibration-only')
        if a.budget is None:p.error('--budget required')
        report=audit_budget(a.results,a.budget,a.frozen)
    else:
        if a.analysis is None:p.error('--analysis required')
        data,report=verify_files(a.results,a.frozen,collect_budget_findings=a.collect_budget_findings)
        answer=read(a.analysis)
        require(answer['results_sha256']==digest(a.results),'Analysis source hash')
        report['statistics']=audit_statistics(data,answer)
        report['analysis_sha256']=digest(a.analysis)
    with (Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json').open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:report[k] for k in ('status','phase','rows')}))


if __name__=='__main__':main()
