"""Independent read-only verification of T1-B outcomes and evidence gaps."""
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext.masbench_t1a_evidence_audit import canonical_sha, read_chain, require, sha_bytes

RUN_ID = 'hpc-masbench-t1b-live-v3-20261118'


def verify_barriers(control, ledger):
    barriers = []
    for row in ledger:
        event = row['event']
        if event['kind'] != 'barrier':
            continue
        receipt = event['receipt']
        proof = control[receipt['control_event_seq']]
        marker = proof['event']
        require(proof['hash']==receipt['control_event_hash'] and marker['kind']=='unload-complete',
                'barrier hash mismatch')
        obs = marker['observation']
        require(obs['ledger_seq']==row['seq'] and obs['ledger_tip']==row['previous'], 'stale barrier')
        require(obs['response'].get('done') is True and obs['response'].get('done_reason')=='unload'
                and obs['ps'].get('models')==[] and obs['process_observations']
                and all(item['stamp']!=item['observed_stamp'] for item in obs['process_observations']),
                'runner disappearance was not observed')
        barriers.append(proof)
    return barriers


def verify_cases(control, ledger, plan):
    events = [row['event'] for row in control]
    starts = [i for i,event in enumerate(events) if event['kind']=='case-start']
    ends = [i for i,event in enumerate(events) if event['kind']=='case-end']
    require(len(starts)==len(ends)==4, 'not four terminal cases')
    require([events[i]['id'] for i in starts]==[x['id'] for x in plan['cases']], 'case order')
    requests = [row['event'] for row in ledger if row['event']['kind']=='request']
    settlements = {row['event']['id']:row['event'] for row in ledger if row['event']['kind']=='finish'}
    require(len(requests)==len(settlements)==4, 'request/settlement count')
    require(len({r['id'] for r in requests})==4, 'repeated request ID')
    rows = []
    for case,start,end,r in zip(plan['cases'],starts,ends,requests,strict=True):
        result = settlements[r['id']]
        require(start < end and events[end]['id']==case['id'] and events[end]['request_id']==r['id'],
                'case does not match settlement')
        require(r['input']+r['output']<=plan['runtime']['context'] and r['output']==case['max_output'],
                'window or output cap exceeded')
        seq = events[start:end]
        if case['fault']=='none':
            usage = result['usage']
            require(result['status']=='completed' and usage['prompt_tokens']==r['input']
                    and 0<=usage['completion_tokens']<=r['output'], 'normal count mismatch')
        else:
            expected='timeout' if case['fault']=='timeout' else 'interrupted'
            require(result['status']==expected and result['usage'] is None, 'unknown usage was not retained')
            names=[row['kind'] for row in seq]
            marker='rpc-timeout' if expected=='timeout' else 'controller-exit'
            order=[names.index(name) for name in ['fault-trigger-armed',marker,'unload-start','unload-complete',
                                                  'dispatch-permit-evaluated']]
            require(order==sorted(order) and seq[order[-1]]['permitted'], 'fault and recovery order')
            require(any(e['kind']=='http-sent' for e in seq[:order[0]]), 'send not observed before fault')
            require(any(e['kind']=='signal' and e['sent'] and e['signal'] in [15,9]
                        for e in seq[order[1]:order[2]]), 'owned HTTP worker signal missing')
            if expected=='interrupted':
                require(any(e['kind']=='controller-signal' and e['signal']==int(signal.SIGKILL)
                            for e in seq[:order[1]]), 'owned controller termination missing')
        rows.append({'id':case['id'],'request_id':r['id'],'status':result['status'],
                     'reserved_input':r['input'],'reserved_output':r['output'],'usage':result['usage']})
    return rows


def verify_watchdog_block(control, ledger, plan, summary, directory):
    """Verify the observed prefix and distinguish a recorded gate from valid proof."""
    starts = [r for r in control if r['event']['kind']=='case-start']
    ends = [r['event'] for r in control if r['event']['kind']=='case-end']
    require([r['event']['id'] for r in starts]==['normal','watchdog']
            and [e['id'] for e in ends]==['normal'], 'unexpected failed prefix')
    negative = control[:starts[0]['seq']]
    require(any(r['event']['kind']=='overflow-blocked-before-http' for r in negative)
            and not any(r['event']['kind'] in ('charge','http-sent') for r in negative), 'overflow reached HTTP')
    counts = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-full-input-count.json'))]
    bindings = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-binding-evidence.json'))]
    payloads = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-provider-request.json'))]
    clients = [x['data'] for p in sorted(directory.glob('*-client.json'))
               if (x := json.loads(p.read_bytes()))['phase']=='completed']
    request_rows = [r for r in ledger if r['event']['kind']=='request']
    finish_rows = [r for r in ledger if r['event']['kind']=='finish']
    require(len(counts)==3 and counts[0]['row']['token_count']+32>plan['runtime']['context'],
            'negative window counter')
    require(len(bindings)==len(payloads)==len(clients)==len(request_rows)==len(finish_rows)==2,
            'missing evidence for dispatched requests')
    sends, cases = [], []
    for case,count,binding,provider,client,reservation,finish in zip(
            plan['cases'][:2],counts[1:],bindings,payloads,clients,request_rows,finish_rows,strict=True):
        request, result, payload = reservation['event'], finish['event'], provider['payload']
        require(reservation['seq']<finish['seq'] and request['id']==result['id']==provider['request_id'],
                'reservation and settlement mismatch')
        require(case['messages']==payload['messages']==count['messages']
                and canonical_sha(payload)==client['payload_sha256']
                and canonical_sha(binding)==client['context_evidence_sha256']
                and canonical_sha(case['messages'])==binding['input_sha']==client['request_sha256'],
                'frozen messages or ContextBinding hash mismatch')
        models = binding['ps']['models']
        require(len(models)==1 and models[0]['name']==payload['model']==plan['runtime']['model']
                and models[0]['digest']==client['observed_identity']['manifest_sha256']==client['manifest_sha256']
                and models[0]['context_length']==plan['runtime']['context']
                and binding['version']['version']==plan['runtime']['version'], 'live model identity or context')
        require(count['row']['rendered']==binding['debug']['_debug_info']['rendered_template']
                and count['row']['token_count']==request['input']==client['prompt_tokens_preflight']
                and payload['max_tokens']==case['max_output']==request['output']
                and request['input']+request['output']<=plan['runtime']['context'], 'full render or window')
        wire_hash = canonical_sha({'kind':'http','method':'POST','path':'/v1/chat/completions','body':payload,
            'authorization':str(ROOT/'research/protocols/masbench_t1b_execution_authorization.json')})
        send, = [r for r in control if r['event']['kind']=='http-sent' and r['event']['request_sha256']==wire_hash]
        sends.append(send)
        if case['fault']=='none':
            usage = result['usage']
            response = client['response']
            require(result['status']=='completed' and response['choices'][0]['finish_reason']=='stop'
                    and response['choices'][0]['message']['content']=='OK'
                    and usage['prompt_tokens']==request['input'] and usage['completion_tokens']<=request['output']
                    and all(response['usage'][k]==client['usage'][k]==v for k,v in usage.items()),
                    'normal response or usage mismatch')
        else:
            require(result['status']=='timeout' and result['usage'] is client['usage'] is None
                    and result['uncertain'] and client['error']=='timeout', 'timeout usage policy')
        cases.append({'id':case['id'],'status':result['status'],'reserved_input':request['input'],
                      'reserved_output':request['output'],'usage':result['usage']})
    suffix = control[sends[-1]['seq']+1:]
    kinds = ['fault-trigger-armed','rpc-timeout','client-failure','unload-start','unload-complete',
             'dispatch-permit-evaluated']
    timeline = {kind:next(row for row in suffix if row['event']['kind']==kind) for kind in kinds}
    require([v['seq'] for v in timeline.values()]==sorted(v['seq'] for v in timeline.values()),
            'watchdog, unload or permit out of order')
    timeout = timeline['rpc-timeout']
    pid = sends[-1]['event']['pid']
    require(timeout['event']['pid']==pid and timeout['event']['sent_observed'], 'timeout worker mismatch')
    signals = [r for r in suffix if r['event']['kind']=='signal' and r['event']['pid']==pid and r['event']['sent']]
    require([r['event']['signal'] for r in signals]==[15,9]
            and all(timeout['seq']<r['seq']<timeline['unload-start']['seq'] for r in signals), 'missing actual worker signals')
    worker_end, = [r for r in suffix if r['event']['kind']=='rpc-end' and r['event']['pid']==pid]
    require(not any(r['event']['kind']=='generation-result-observed' for r in suffix), 'terminal generation result was observed')
    before_unload = [r['event']['data']['value'] for r in suffix if r['seq']<timeline['unload-start']['seq']
                     and r['event']['kind']=='cleanup-rpc' and r['event']['data']['phase']=='result']
    finished = timeline['unload-complete']
    observation = finished['event']['observation']
    barrier, = [r for r in ledger if r['event']['kind']=='barrier']
    require(barrier['event']['receipt']=={'control_event_seq':finished['seq'],'control_event_hash':finished['hash']}
            and observation['ledger_seq']==barrier['seq'] and observation['ledger_tip']==barrier['previous'],
            'recorded barrier does not bind to unload evidence')
    permit = timeline['dispatch-permit-evaluated']['event']
    require(before_unload==[{'models':[]}] and observation['ps']['models']==[]
            and observation['response']['done'] is True and observation['response']['done_reason']=='unload'
            and timeline['unload-start']['event']['old_runners']==observation['process_observations']==[]
            and permit['permitted'] is True and permit['charged_requests']==2
            and permit['charged_outputs']==sum(row['reserved_output'] for row in cases)
            and summary['error']=='SafetyError: no owned runner observed through unload',
            'missing expected blocked-run evidence')
    clock = ledger[0]['event']
    def utc_estimate(row):
        return datetime.fromtimestamp(clock['started_utc']+row['mono']-clock['started_mono'], timezone.utc).isoformat()
    return {
        'acceptance_passed':False, 'cases':cases, 'http_send_monotonic':sends[-1]['mono'],
        'overflow_full_input_tokens':counts[0]['row']['token_count'],
        'control_timeline':timeline, 'actual_client_worker_signals':signals, 'client_worker_exit':worker_end,
        'utc_estimates':{kind:utc_estimate(row) for kind,row in timeline.items()}
                        | {'watchdog-http-sent':utc_estimate(sends[-1])}
                        | {f"signal-{r['event']['signal']}":utc_estimate(r) for r in signals},
        'unload_api_acknowledged':True, 'resident_models_empty_before_and_after_unload':True,
        'runner_exit_verified':False, 'ledger_recorded_permit_true':True, 'valid_dispatch_recovery_proven':False,
        'undispatched_cases':['controller','recovery'],
    }


def main():
    require_hpc()
    run = ROOT/'research/sync/runs'/RUN_ID
    status = json.loads((run/'status.json').read_bytes())['status']
    require(status in ('completed','failed'), 'run not terminal')
    artifacts = json.loads((run/'artifacts.json').read_bytes())['files']
    for entry in artifacts:
        data=(run/entry['path']).read_bytes()
        require(len(data)==entry['size'] and sha_bytes(data)==entry['sha256'], 'artifact digest drift')
    out = run/'outputs'
    driver = out/'driver'
    ledger = read_chain(driver/'campaign/ledger.jsonl')
    control = read_chain(driver/'control.jsonl')
    snapshot = json.loads((run/'source_snapshot.json').read_bytes())
    relative='research/protocols/masbench_t1b_synthetic_execution_plan.json'
    plan_bytes=(ROOT/relative).read_bytes()
    entry=next(x for x in snapshot['files'] if x['path']==relative)
    require(entry['remote_sha256']==sha_bytes(plan_bytes),'current plan not run-bound')
    plan=json.loads(plan_bytes)
    require(ledger[0]['event']['binding']==control[0]['event']['identity'], 'journal identity mismatch')
    directory=driver/'campaign/artifacts'
    rows = {path.name:path for path in directory.iterdir()}
    for event in (x['event'] for x in ledger if x['event']['kind']=='bytes'):
        data=rows[event['path']].read_bytes()
        require(len(data)==event['count'] and sha_bytes(data)==event['sha256'],'ledger artifact mismatch')
    charges = {key:0 for key in ['get','cleanup_get','debug','unload']}
    for event in (x['event'] for x in control):
        if event['kind']=='charge':
            charges[event['category']]+=1
    require(all(charges[k]<=plan['caps'][k] for k in charges), 'HTTP budget exceeded')
    require(sum(a['size'] for a in artifacts) <= plan['caps']['artifact_bytes'], 'artifact cap exceeded')
    summary = json.loads((out/'summary.json').read_bytes())
    require(summary['control_counts']==charges and summary['actual_task_inputs']==0, 'summary counts mismatch')
    patch = json.loads((run/'manifest.json').read_bytes())['source_changes']
    compressed = (run/patch['path']).read_bytes()
    require(sha_bytes(compressed)==patch['sha256'] and len(compressed)==patch['size'], 'snapshot archive digest')
    restored = gzip.decompress(compressed)
    require(sha_bytes(restored)==patch['original_sha256'] and len(restored)==patch['original_size'], 'raw patch digest')
    output = Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json'
    if status=='failed':
        result=verify_watchdog_block(control,ledger,plan,summary,directory)
        totals={key:sum(row['reserved_'+key] for row in result['cases']) for key in ['input','output']}
        require(all(totals[k]==summary['reservations'][k+'s'] for k in totals)
                and totals['input']<=plan['caps']['inputs'] and totals['output']<=plan['caps']['outputs'],
                'failed-run budget mismatch')
        observation_path = ROOT/'research/logs/masbench-t1-driver-2026-11-17/t1b_service_observations_localtime.json'
        service_bytes = observation_path.read_bytes()
        service = json.loads(service_bytes)
        service_generation = [r for r in service['service_routes'] if r['route']=='/v1/chat/completions']
        require([r['status'] for r in service_generation]==[200,499]
                and len(service['service_routes'])==sum(charges.values())+2
                and any(r['event']=='context_canceled' for r in service['runner_log_events']),
                'bounded server telemetry did not corroborate both calls')
        write_json(output,dict(result,source_run=RUN_ID,artifacts_verified=len(artifacts),charges=charges,
                    total_reservations=totals,service_generation_log=service_generation,
                    service_excerpt_sha256=sha_bytes(service_bytes),
                    native_immediate_idle_verified=False,real_task_inputs=0))
        return
    barriers=verify_barriers(control,ledger)
    require(len(barriers)==3,'expected two recovery barriers and final unload')
    cases=verify_cases(control,ledger,plan)
    counts = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-full-input-count.json'))]
    bindings = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-binding-evidence.json'))]
    require(len(counts)==5 and len(bindings)==4 and counts[0]['row']['token_count']+32>1024, 'missing negative/bindings')
    for count, binding, case, result in zip(counts[1:],bindings,plan['cases'],cases,strict=True):
        require(case['messages']==count['messages'] and canonical_sha(case['messages'])==binding['input_sha'],
                'complete input not preserved')
        require(binding['debug']['_debug_info']['rendered_template']==count['row']['rendered']
                and count['row']['token_count']==result['reserved_input']
                and binding['ps']['models'][0]['context_length']==1024, 'render/count/context mismatch')
    totals={key:sum(x[key] for x in cases) for key in ['reserved_input','reserved_output']}
    require(totals['reserved_input']<=4096 and totals['reserved_output']==1088, 'token budget mismatch')
    write_json(output,{
        'source_run':RUN_ID, 'artifacts_verified':len(artifacts), 'cases':cases, 'charges':charges,
        'total_reservations':totals, 'unload_barriers':len(barriers),
        'acceptance_passed':True, 'native_immediate_idle_verified':False, 'real_task_inputs':0,
    })


if __name__ == '__main__':
    main()
