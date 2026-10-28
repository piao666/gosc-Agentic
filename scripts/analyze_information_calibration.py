"""HPC-only predeclared paired analysis for GP-ID-CAL-v1 exploratory data."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _endpoint(estimate, samples, plan, family):
    valid = np.isfinite(samples)
    undefined = int((~valid).sum())
    status = 'defined'
    ci95 = ci_family = None
    if estimate is None or not math.isfinite(estimate) or undefined:
        status = 'undefined'
    else:
        ci95 = np.quantile(samples, [.025,.975], method=plan['quantile_method']).tolist()
        if family:
            tail = plan['alpha'] / (2 * plan['primary_endpoint_family'])
            ci_family = np.quantile(samples, [tail,1-tail], method=plan['quantile_method']).tolist()
        if np.ptp(samples) == 0:
            status = 'degenerate'
    return dict(estimate=estimate,ci95=ci95,ci_family=ci_family,status=status,
                bootstrap_valid=int(valid.sum()),bootstrap_undefined=undefined)


def compare_pair(treatment, control, indices, plan, family=True):
    gain = control['time'] - treatment['time']
    endpoints = {'gain':_endpoint(float(gain.mean()),gain[indices].mean(axis=1),plan,family)}
    for key in ('comm','cpu'):
        denominator = float(control[key].mean())
        estimate = float(treatment[key].mean()/denominator) if denominator > 0 else None
        with np.errstate(divide='ignore',invalid='ignore'):
            samples = treatment[key][indices].mean(axis=1) / control[key][indices].mean(axis=1)
        endpoints[key+'_ratio'] = _endpoint(estimate,samples,plan,family)
    ratios = [endpoints[k]['estimate'] for k in ('comm_ratio','cpu_ratio')]
    support = all(v is not None and plan['minimum_matched_ratio'] <= v <= plan['maximum_resource_ratio'] for v in ratios)
    interval = 'ci_family' if family else 'ci95'
    noninferior = (all(e['status']=='defined' for e in endpoints.values())
        and endpoints['gain'][interval][0] >= plan['minimum_task_gain_slots']
        and all(endpoints[k][interval][1] <= plan['maximum_resource_ratio'] for k in ('comm_ratio','cpu_ratio')))
    return dict(**endpoints,mean_joint_cost_support=support,
                noninferiority_screen=bool(noninferior),matched_screen=bool(noninferior and support))


def vectors(data):
    plan = data['frozen']['plan']
    if data.get('phase')!='calibration' or not data.get('calibration_run') or data.get('formal_test_run') or data.get('training'):
        raise ValueError('Not an authorized exploratory calibration matrix')
    seeds = plan['calibration_seeds']
    ids = [c['id'] for c in data['frozen']['cases']]
    index = {(r['seed'],r['case_id']):r for r in data['rows']}
    if len(index)!=len(data['rows']) or set(index)!={(s,c) for s in seeds for c in ids}:
        raise ValueError('Incomplete or duplicate calibration matrix')
    out = {}
    for case in ids:
        rows = [index[seed,case] for seed in seeds]
        for row in rows:
            result = row['result']
            if row['status']!='completed' or not 0 <= result['completion_time'] <= plan['calibration_steps']:
                raise ValueError('Software failed/invalid completion row')
            if not result['completed'] and result['completion_time']!=plan['calibration_steps']:
                raise ValueError('Unexplained early truncation')
            if result['completed'] != (result['found']==8):
                raise ValueError('Task completion/found mismatch')
        costs = [r['result']['service']['cost'] for r in rows]
        out[case] = dict(time=np.array([r['result']['completion_time'] for r in rows],dtype=float),
            comm=np.array([c['ul_uses']+c['dl_uses'] for c in costs],dtype=float),
            cpu=np.array([c['cpu_seconds'] for c in costs],dtype=float),rows=rows)
        for key in ('time','comm','cpu'):
            if not np.isfinite(out[case][key]).all() or (out[case][key]<0).any():
                raise ValueError('Nonfinite/negative observed endpoint')
    return out


def analyze(data):
    plan = data['frozen']['plan']; by_case = vectors(data)
    n = len(plan['calibration_seeds'])
    if n!=plan['calibration_N'] or n!=12 or len(by_case)!=13:
        raise ValueError('Changed exploratory N/case set')
    indices = np.random.default_rng(plan['analysis_seed']).integers(0,n,
                 size=(plan['bootstrap_resamples'],n),dtype=np.int64)
    descriptions = []
    for name, values in by_case.items():
        item = dict(id=name,N=n,completed=sum(r['result']['completed'] for r in values['rows']),
            not_completed=sum(not r['result']['completed'] for r in values['rows']),
            false_declarations=sum(r['result']['false_declarations'] for r in values['rows']),
            mean_mission_wall_seconds=float(np.mean([r['mission_wall_seconds'] for r in values['rows']])),
            mean_end_to_end_wall_seconds=float(np.mean([r['end_to_end_wall_seconds'] for r in values['rows']])),
            mean_recording_process_seconds=float(np.mean([r['process_seconds'] for r in values['rows']])))
        for key in ('time','comm','cpu'):
            arr = values[key]
            item['mean_'+key] = float(arr.mean())
            q = np.quantile(arr,[0,.25,.5,.75,.9,1.],method=plan['quantile_method'])
            item[key+'_quantiles'] = dict(zip(('min','p25','p50','p75','p90','max'),map(float,q)))
        descriptions.append(item)
    comparisons = {}
    for group, family in (('primary_comparisons',True),('secondary_comparisons',False)):
        comparisons[group] = [dict(id=c['id'],treatment=c['treatment'],control=c['control'],
            **compare_pair(by_case[c['treatment']],by_case[c['control']],indices,plan,family)) for c in plan[group]]
    primary_index = {c['id']:c for c in comparisons['primary_comparisons']}
    eligible = all(primary_index[k]['matched_screen'] for k in plan['primary_method_comparison_ids'])
    return dict(status='eligible_for_future_formal_protocol_review' if eligible else 'No-Go',
        scope=plan['scope'],primary_method=plan['primary_method'],N=n,missions=len(data['rows']),
        bootstrap_resamples=plan['bootstrap_resamples'],analysis_seed=plan['analysis_seed'],
        bootstrap_index_sha256=hashlib.sha256(indices.tobytes()).hexdigest(),
        family_endpoints=plan['primary_endpoint_family'],quantile_method=plan['quantile_method'],
        cases=descriptions,primary=comparisons['primary_comparisons'],secondary=comparisons['secondary_comparisons'],
        primary_method_eligible=eligible,timestamp_screen=primary_index['timestamp_use']['matched_screen'],
        formal_test_N=None,formal_test_run=False,training=False,
        limitations='Exploratory N12 at one fixed working point, bootstrap approximations; no equivalence/zero-value inference, formal significance, full cost frontier or single-message direct causal effect. No arm selected by observed task outcomes.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    a = parser.parse_args()
    if os.name!='posix' or os.getuid()!=8301880 or str(ROOT)!='/home/u202520081000097/jupyterlab/Paper/gosc':
        raise RuntimeError('HPC-only')
    if not os.environ.get('GOSC_RUN_DIR') or not os.environ.get('GOSC_OUTPUT_DIR'):
        raise RuntimeError('Registered runner required')
    data = json.loads(a.results.read_text())
    answer = analyze(data)
    answer['results_sha256'] = hashlib.sha256(a.results.read_bytes()).hexdigest()
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    with (out/'analysis.json').open('x') as stream:
        json.dump(answer,stream,indent=2,allow_nan=False);stream.write('\n')
    text = '# GP-ID-CAL-v1 exploratory calibration\n\nN=12 fresh worlds; single fixed working point. '+answer['status']+'\n\n'
    text += '| Comparison | Gain slots (95% exploratory CI) | Comm ratio | Logical CPU ratio | Matched support | Family screen |\n|---|---|---:|---:|---|---|\n'
    for c in answer['primary']:
        text += '| {} | {} {} | {} | {} | {} | {} |\n'.format(c['id'],c['gain']['estimate'],c['gain']['ci95'],
            c['comm_ratio']['estimate'],c['cpu_ratio']['estimate'],c['mean_joint_cost_support'],c['matched_screen'])
    text += '\nAll family intervals, quantiles, censoring and secondary diagnostics are in analysis.json. No formal test/training run.\n'
    (out/'calibration.md').write_text(text)
    print(json.dumps(dict(status=answer['status'],N=answer['N'],missions=answer['missions'],formal_test=False)))


if __name__=='__main__':
    main()
