"""Independently audit the bounded cold-load diagnostic, including partial runs."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext import masbench_t1_cold_load as diag
from experiments_ext.masbench_t1_runner_evidence_audit import verify_artifacts
from experiments_ext.masbench_t1a_evidence_audit import read_chain, require
from extensions.masbench_reasoning.execution_safety import digest


def progress(log_begin,log_end):
    if not log_begin or log_begin['inode']!=log_end['inode']:
        return {'status':'unknown-log-window','events':[]}
    if not 0<=log_end['offset']-log_begin['offset']<=512*1024:
        return {'status':'window-outside-cap','events':[]}
    if diag.LOG.stat().st_ino!=log_begin['inode']:
        return {'status':'log-rotated','events':[]}
    labels={
        b'starting runner':'runner-command',
        b'starting go runner':'runner-init',
        b'load_tensors':'weight-tensors',
        b'llama runner started in':'runner-ready',
        b'Load failed':'load-failed',
        b'client connection closed before server finished loading':'client-cancel-during-load',
    }
    events=[]
    last_timestamp=None
    pending=[]
    with diag.LOG.open('rb') as stream:
        stream.seek(log_begin['offset'])
        data=stream.read(log_end['offset']-log_begin['offset'])
    offset=log_begin['offset']
    for line in data.splitlines(keepends=True):
        match=re.search(rb'\btime=(\d{4}-\d\d-\d\dT[^\s]+)',line)
        if match:
            last_timestamp=match[1].decode()
            for row in pending:
                row['timestamp_ceiling']=last_timestamp
            pending.clear()
        names=[label for value,label in labels.items() if value in line]
        route=re.search(rb'\[GIN\].*?\|\s*(\d+)\s*\|\s*([^|]+)\|.*?\b(POST)\s+"(/[^"]+)"\s*$',line)
        if names or route:
            row={'events':names,'offset':offset,'bytes':len(line),'sha256':hashlib.sha256(line).hexdigest()}
            if match:
                row['timestamp']=last_timestamp
            else:
                row['timestamp_floor']=last_timestamp
                pending.append(row)
            if route:
                row.update(http_status=int(route[1]),http_elapsed=route[2].decode().strip(),route=route[4].decode())
            events.append(row)
        offset+=len(line)
    return {'status':'bounded-window-read','events':events,'sha256':hashlib.sha256(data).hexdigest()}


def summarize_samples(path):
    if not path.exists():
        return [], []
    samples = [json.loads(line) for line in path.read_bytes().splitlines()]
    by_identity={}
    for sample in samples:
        for runner in sample['runners']:
            key=(runner['pid'],runner['stamp'])
            by_identity.setdefault(key,[]).append(dict(runner,observed_mono=sample['mono']))
    results=[]
    for (pid,stamp),rows in by_identity.items():
        mapped=[r['observed_mono'] for r in rows if r.get('model_mapped')]
        observed=[r for r in rows if 'io' in r]
        delta={}
        if len(observed)>1:
            for key in observed[0]['io'].keys() & observed[-1]['io'].keys():
                delta[key]=observed[-1]['io'][key]-observed[0]['io'][key]
        results.append({'pid':pid,'stamp':stamp,'first_sample':rows[0],'last_sample':rows[-1],
                        'samples':len(rows),'io_samples':len(observed),'observed_counter_deltas':delta,
                        'first_model_mapping_observed_mono':min(mapped) if mapped else None})
    return samples,results


def main():
    require_hpc()
    run=diag.RUNS/diag.RUN
    files=verify_artifacts(run)
    output=run/'outputs'
    result=json.loads((output/'summary.json').read_bytes())
    history=read_chain(output/'control.jsonl')
    charges=dict.fromkeys(diag.CAPS,0)
    sent=[]
    witnesses=[]
    cleanup=[]
    for row in history:
        event=row['event']
        kind=event['kind']
        if kind=='charge':
            charges[event['category']]+=1
        if kind=='worker':
            method,path,body=diag.request_spec(event['operation'])
            require(event['request_sha256']==digest({'method':method,'path':path,'body':body}),'wire identity changed')
        if kind=='http-sent':
            sent.append(event)
        if kind=='runner-observed':
            witnesses.append(dict(event['runner'],observed_mono=row['mono']))
        if kind=='unload-and-identity-proved':
            cleanup.append(event)
    require(charges==result['charges'] and all(value<=diag.CAPS[key] for key,value in charges.items()),'HTTP budget drift')
    require(result['prior_old_get_charge']+charges['old_get']<=3,'cumulative marker GET budget')
    render=[e for e in sent if e['operation']=='render']
    require(len(render)<=1 and result['generation_requests']==result['actual_task_inputs']==0,'render-only scope')
    samples,runner_summary=summarize_samples(output/'samples.jsonl')
    require(len(samples)==result['samples'],'sample count')
    logfile=progress(result['log_begin'],result['log_end'])
    report={'run':diag.RUN,'registered_output_files_verified':len(files),'generation_requests':0,'real_task_inputs':0,
            'render':result['render'],'render_error':result.get('render_error'),'campaign_error':result.get('error'),
            'render_send':render[0] if render else None,'runner_witnesses':witnesses,'runner_samples':runner_summary,
            'sample_count':len(samples),'charges':charges,'service_log':logfile,
            'combined_old_get_charges':result['prior_old_get_charge']+charges['old_get'],
            'service_marker_retained':result['service_marker_retained'],'cleanup_proof':cleanup,
            'total_seconds':result['elapsed_seconds'],'peaks':result['peaks'],
            'physical_read_attribution_verified':False,'native_immediate_idle_verified':False,'t1_acceptance_passed':False}
    if render:
        report['elapsed_from_send_to_observed_end_seconds']=result['render_finished']['mono']-render[0]['mono']
        origin=datetime.fromisoformat(render[0]['utc'])
        if witnesses:
            report['first_runner_observed_seconds']=witnesses[0]['observed_mono']-render[0]['mono']
        for event in logfile['events']:
            for source,target in [('timestamp','seconds_after_send'),('timestamp_floor','seconds_floor'),
                                  ('timestamp_ceiling','seconds_ceiling')]:
                if event.get(source):
                    event[target]=(datetime.fromisoformat(event[source])-origin).total_seconds()
    write_json(Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json',report)


if __name__=='__main__':
    main()
