"""Verify the post-storage T1-B failure without contacting or loading Ollama."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext.masbench_t1_runner_evidence_audit import AUTH, LIVE, PLAN, verify_artifacts
from experiments_ext.masbench_t1a_evidence_audit import canonical_sha, read_chain, require, sha_bytes


def service_observations():
    log = ROOT/'.local/ollama/service.log'
    time_window = re.compile(rb'2026[-/]11[-/]19(?:T| - )(?:10:59:5[7-9]|11:00:[0-5][0-9]|02:59:5[7-9]|03:00:[0-5][0-9])')
    watched = {
        b'starting runner':'runner command started',
        b'starting go runner':'Go runner starting',
        b'new model will fit':'memory estimate fit',
        b'Load failed':'load failed',
        b'context canceled':'request context canceled',
        b'llama runner started in':'runner ready',
        b'client connection closed before server finished loading':'client disconnected during loading',
    }
    rows = []
    with log.open('rb') as stream:
        while line := stream.readline():
            match = time_window.search(line)
            if not match:
                continue
            events = [value for key,value in watched.items() if key in line]
            route = re.search(rb'\[GIN\].*?\|\s*(\d+)\s*\|\s*([^|]+)\|.*?\b(GET|POST)\s+"(/[^"]+)"\s*$',line)
            if route and route[4] in (b'/api/ps',b'/api/chat',b'/v1/chat/completions'):
                events.append({'status':int(route[1]),'duration':route[2].decode().strip(),
                               'method':route[3].decode(),'path':route[4].decode()})
            if events:
                rows.append({'time':match[0].decode(),'offset':stream.tell()-len(line),'bytes':len(line),
                             'sha256':hashlib.sha256(line).hexdigest(),'events':events})
    return rows


def main():
    require_hpc()
    run = ROOT/'research/sync/runs'/LIVE
    status = json.loads((run/'status.json').read_bytes())
    require(status['status']=='failed' and status['exit_code']==1,'unexpected source run status')
    artifacts = verify_artifacts(run)
    plan_body = (ROOT/PLAN).read_bytes()
    snapshot = json.loads((run/'source_snapshot.json').read_bytes())['files']
    require(next(row for row in snapshot if row['path']==PLAN)['remote_sha256']==sha_bytes(plan_body),'plan not bound')
    plan = json.loads(plan_body)
    root = run/'outputs/driver'
    control = read_chain(root/'control.jsonl')
    ledger = read_chain(root/'campaign/ledger.jsonl')
    require(ledger[0]['event']['binding']==control[0]['event']['identity'],'journal identity mismatch')
    require(not any(row['event']['kind'] in ('request','finish','barrier') for row in ledger),'generation or recovery recorded')
    for row in ledger:
        event = row['event']
        if event['kind']=='bytes':
            blob = (root/'campaign/artifacts'/event['path']).read_bytes()
            require(len(blob)==event['count'] and sha_bytes(blob)==event['sha256'],'ledger artifact mismatch')
    require([r['event']['id'] for r in control if r['event']['kind']=='case-start']==['normal'],'unexpected cases')
    timeout, = [r for r in control if r['event']['kind']=='rpc-timeout']
    worker = timeout['event']['pid']
    spawn, = [r for r in control if r['event']['kind']=='rpc-spawn' and r['event']['pid']==worker]
    sent, = [r for r in control if r['event']['kind']=='http-sent' and r['event']['pid']==worker]
    spec = {'kind':'http','method':'POST','path':'/api/chat','authorization':str(ROOT/AUTH),
            'body':{'model':plan['runtime']['model'],'messages':plan['cases'][0]['messages'],'stream':False,
                    '_debug_render_only':True,'options':{'num_thread':2}}}
    require(spawn['event']['request_sha256']==sent['event']['request_sha256']==canonical_sha(spec)
            and timeout['event']['sent_observed'] and spawn['seq']<sent['seq']<timeout['seq'],'render dispatch identity')
    require(0<=timeout['mono']-spawn['event']['deadline_monotonic']<1,'deadline evidence invalid')
    require(plan['caps']['operation']==60 and 30<timeout['mono']-sent['mono']<=60,'render still has an early timeout')
    signals = [r for r in control if r['event']['kind']=='signal' and r['event']['pid']==worker and r['event']['sent']]
    require(signals and all(r['seq']>timeout['seq'] for r in signals),'missing actual worker signal')
    cleanup, = [r for r in control if r['event']['kind']=='unload-unverified']
    proof = cleanup['event']['observation']
    require(proof['response']['done_reason']=='unload' and proof['ps']=={'models':[]}
            and proof['process_observations']==[] and proof['remaining_runners']==[],'cleanup state mismatch')
    require(not any(r['event']['kind'] in ('runner-observed','runner-dispatch-bound','dispatch-permit-evaluated',
                                          'unload-complete','generation-result-observed') for r in control),
            'unexpected successful binding, generation or permit')
    summary = json.loads((run/'outputs/summary.json').read_bytes())
    require(summary['reservations']=={'inputs':0,'outputs':0,'requests':{}} and summary['service_marker_retained']
            and summary['actual_task_inputs']==0 and summary['cases']==[],'summary mismatch')
    require(all(peak<=plan['caps'][name] for name,peak in summary['sampled_peaks'].items()),'sampled resource cap')
    service = service_observations()
    write_json(Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json',{
        'source_run':LIVE,'source_run_failed':True,'acceptance_passed':False,'artifacts_verified':len(artifacts),
        'ledger_tip':ledger[-1]['hash'],'control_tip':control[-1]['hash'],
        'cold_debug_wait_seconds':timeout['mono']-sent['mono'],'timeout':timeout,'actual_signals':signals,
        'unload_unverified':cleanup,'service_log_projection':service,'generation_requests':0,'real_task_inputs':0,
        'next_dispatch_allowed':False,'native_immediate_idle_verified':False,
    })


if __name__=='__main__':
    main()
