"""Independently verify T1 runner observations and dispatch gates from journals."""
import argparse
import gzip
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext.masbench_t1a_evidence_audit import canonical_sha, read_chain, require, sha_bytes
from experiments_ext.masbench_t1b_evidence_audit import verify_cases

LIVE = 'hpc-masbench-t1b-post-storage-20261119'
FIXTURE = 'hpc-masbench-t1-runner-recovery-contract-v2-20261118'
PLAN = 'research/protocols/masbench_t1b_post_storage_plan.json'
AUTH = 'research/protocols/masbench_t1b_post_storage_authorization.json'


def verify_artifacts(run):
    entries = json.loads((run/'artifacts.json').read_bytes())['files']
    for row in entries:
        data = (run/row['path']).read_bytes()
        require(len(data)==row['size'] and sha_bytes(data)==row['sha256'], 'run artifact mismatch')
    record = json.loads((run/'manifest.json').read_bytes())['source_changes']
    compressed = (run/record['path']).read_bytes()
    raw = gzip.decompress(compressed)
    require(len(raw)==record['original_size'] and sha_bytes(raw)==record['original_sha256']
            and len(compressed)==record['size'] and sha_bytes(compressed)==record['sha256'], 'source patch mismatch')
    return entries


def prove_barriers(control, ledger):
    proofs = []
    for row in ledger:
        event = row['event']
        if event['kind']!='barrier':
            continue
        receipt = event['receipt']
        stop = control[receipt['control_event_seq']]
        require(stop['event']['kind']=='unload-complete' and receipt['control_event_hash']==stop['hash'],
                'barrier receipt mismatch')
        obs = stop['event']['observation']
        claim = next(x for x in reversed(control[:stop['seq']]) if x['event']['kind']=='service-claimed')
        epoch = control[claim['seq']+1:stop['seq']]
        start, = [x for x in epoch if x['event']['kind']=='unload-start']
        prior = [x['event'] for x in epoch if x['seq']<start['seq'] and x['event']['kind']=='runner-observed']
        expected = {(x['runner']['pid'],x['runner']['stamp']) for x in prior}
        observed = {(x['pid'],x['stamp']) for x in obs['process_observations']}
        require(expected and expected==observed and len(observed)==len(obs['process_observations'])
                and all(x['service']==obs['service']==claim['event']['service'] for x in prior)
                and start['event']['old_runners']==[{'pid':p,'stamp':s} for p,s in sorted(expected)]
                and all((x['pid'],x['stamp']) in expected for x in start['event']['present_before_unload']),
                'cleanup lost or substituted a pre-dispatch runner')
        require(obs['ps']=={'models':[]} and obs['remaining_runners']==[]
                and obs['response']['done'] is True and obs['response']['done_reason']=='unload'
                and all(x['stamp']!=x['observed_stamp'] for x in obs['process_observations'])
                and obs['ledger_seq']==row['seq'] and obs['ledger_tip']==row['previous'], 'incomplete exit proof')
        proofs.append({'start':start,'complete':stop})
    return proofs


def inspect_fixture(run):
    tests = {
        'test_early_empty_residency_still_proves_exit_of_pre_dispatch_runner':1,
        'test_empty_runner_witness_blocks_dispatch_and_retains_recovery_lease':0,
        'test_empty_residency_cannot_release_a_surviving_runner':0,
        'test_reused_pid_proves_old_identity_gone_but_is_not_owned':1,
        'test_runner_change_between_attestation_and_dispatch_stops_generation':0,
        'test_resource_verification_failure_after_unload_keeps_fence':0,
        'test_interrupted_inflight_keeps_unknown_cost_and_requires_cleanup':1,
    }
    results = {}
    for name, expected in tests.items():
        fixture = run/'outputs/fixtures'/name/'driver'
        control = read_chain(fixture/'control.jsonl')
        ledger = read_chain(fixture/'campaign/ledger.jsonl')
        require(not any(x['event']['kind']=='http-sent' for x in control), 'fixture sent network HTTP')
        proofs = prove_barriers(control,ledger)
        permits = [x for x in control if x['event']['kind']=='dispatch-permit-evaluated']
        require(len(proofs)==len(permits)==expected and all(r['event']['permitted'] for r in permits),
                'fixture accepted incorrect continuation')
        unknown = [x['event']['id'] for x in ledger if x['event']['kind']=='finish' and x['event']['usage'] is None]
        results[name] = {'proofs':len(proofs),'permit_records':len(permits),'unknown_usage':unknown}
    return {'fixture_campaigns':results,'real_model_calls':0,'native_immediate_idle_verified':False}


def inspect_live(run, artifacts, plan_path=PLAN, auth_path=AUTH, formal=False, failed_final_cleanup=False,
                 verify_runner_reuse=False):
    snapshot = json.loads((run/'source_snapshot.json').read_bytes())['files']
    plan_body = (ROOT/plan_path).read_bytes()
    require(next(x for x in snapshot if x['path']==plan_path)['remote_sha256']==sha_bytes(plan_body), 'plan mismatch')
    plan = json.loads(plan_body)
    driver = run/'outputs/driver'
    control = read_chain(driver/'control.jsonl')
    ledger = read_chain(driver/'campaign/ledger.jsonl')
    require(control[0]['event']['identity']==ledger[0]['event']['binding'], 'run journal binding')
    results = verify_cases(control,ledger,plan)
    proofs = prove_barriers(control,ledger)
    fault_count=sum(case['fault']!='none' for case in plan['cases'])
    require(len(proofs)==fault_count+int(not failed_final_cleanup),'unexpected number of recovery barriers')
    for proof in proofs:
        resources = proof['complete']['event']['observation']['resources_after_unload']
        require(set(resources)=={'driver_rss','service_rss','gpu_bytes'}
                and all(type(v) is int and 0<=v<=plan['caps'][k] for k,v in resources.items()),
                'fresh post-unload resource snapshot missing or outside limits')
    directory = driver/'campaign/artifacts'
    for row in ledger:
        event = row['event']
        if event['kind']=='bytes':
            body = (directory/event['path']).read_bytes()
            require(len(body)==event['count'] and sha_bytes(body)==event['sha256'], 'ledger artifact mismatch')
    count = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-full-input-count.json'))]
    bindings = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-binding-evidence.json'))]
    payloads = [json.loads(p.read_bytes()) for p in sorted(directory.glob('*-provider-request.json'))]
    require(len(count)==len(plan['cases'])+1
            and count[0]['row']['token_count']+plan['overflow']['max_output']>plan['runtime']['context'],
            'overflow control')
    negative = control[:next(x['seq'] for x in control if x['event']['kind']=='case-start')]
    require(any(x['event']['kind']=='overflow-blocked-before-http' for x in negative)
            and not any(x['event']['kind']=='http-sent' for x in negative), 'overflow sent HTTP')
    for case,c,b,p,res in zip(plan['cases'],count[1:],bindings,payloads,results,strict=True):
        bound, = [r for r in control if r['event']['kind']=='runner-dispatch-bound'
                  and r['event']['request_id']==res['request_id']]
        event = bound['event']
        prior = next(x for x in reversed(control[:bound['seq']]) if x['event']['kind']=='runner-observed')['event']
        payload = p['payload']
        require(event['runner']==prior['runner'] and event['service']==prior['service']
                and prior['context_evidence_sha256']==canonical_sha(b)
                and event['payload_sha256']==canonical_sha(payload), 'runner bound to wrong context or payload')
        require(payload['messages']==case['messages']==c['messages']
                and c['row']['rendered']==b['debug']['_debug_info']['rendered_template']
                and c['row']['token_count']==res['reserved_input']
                and payload['max_tokens']==res['reserved_output']
                and b['ps']['models'][0]['context_length']==plan['runtime']['context'], 'complete prompt binding')
        wire_hash = canonical_sha({'kind':'http','method':'POST','path':'/v1/chat/completions',
                                   'body':payload,'authorization':str(ROOT/auth_path)})
        sent, = [r for r in control if r['event']['kind']=='http-sent' and r['event']['request_sha256']==wire_hash]
        require(sent['seq']>bound['seq'], 'wire send preceded runner binding')
        if formal:
            require(0<sent['event']['worker_sent_mono']<=sent['mono'],'worker send time mismatch')
        res.update(runner=event['runner'],sent_monotonic=sent['mono'])
        if verify_runner_reuse:
            render = {'model':payload['model'],'messages':payload['messages'],'stream':False,'_debug_render_only':True}
            render_hash = canonical_sha({'kind':'http','method':'POST','path':'/api/chat','body':render,
                                         'authorization':str(ROOT/auth_path)})
            render_sent, = [r for r in control if r['event']['kind']=='http-sent'
                            and r['event']['request_sha256']==render_hash]
            require(render_sent['seq']<bound['seq'],'default-options render must precede generation')
            checks = [r for r in control if r['event']['kind']=='runner-response-bound'
                      and r['event']['request_id']==res['request_id']]
            if res['status']=='completed':
                check, = checks
                check_event=check['event']
                next_cleanup=next(r for r in control[sent['seq']:] if r['event']['kind']=='unload-start')
                require(sent['seq']<check['seq']<next_cleanup['seq'] and check_event['runner']==event['runner']
                        and check_event['service']==event['service'] and check_event['present_after_response']==[event['runner']],
                        'generation runner changed or response witness is out of order')
                res['runner_after_response']=check_event['present_after_response'][0]
            else:
                require(not checks,'interrupted generation unexpectedly has a response witness')
    summary = json.loads((run/'outputs/summary.json').read_bytes())
    charges = {kind:sum(r['event']['kind']=='charge' and r['event']['category']==kind for r in control)
               for kind in ('get','cleanup_get','debug','unload')}
    expected_status='failed' if failed_final_cleanup else 'synthetic_driver_contract_passed'
    require(charges==summary['control_counts'] and all(charges[k]<=plan['caps'][k] for k in charges)
            and sum(a['size'] for a in artifacts)<=plan['caps']['artifact_bytes']
            and summary['reservations']['inputs']<=plan['caps']['inputs']
            and summary['reservations']['outputs']==plan['caps']['outputs']
            and summary['status']==expected_status and summary['service_marker_retained'] is failed_final_cleanup
            and summary['actual_task_inputs']==0, 'run completion, budget or cleanup mismatch')
    clocks = [r['event'] for r in control if r['event']['kind']=='phase-clock']
    if formal:
        require([c['phase'] for c in clocks]==['prepare','generate']*len(plan['cases']),'phase order')
        for index in range(0,len(clocks),2):
            prepare,generate=clocks[index:index+2]
            require(0<prepare['deadline_mono']-prepare['start_mono']<=150
                    and 0<generate['deadline_mono']-generate['start_mono']<=plan['caps']['operation']
                    and prepare['start_mono']<=generate['start_mono']<=prepare['deadline_mono'],'separate budgets not respected')
        if any(case['fault']=='timeout' for case in plan['cases']):
            watchdog, = [r for r in control if r['event']['kind']=='fault-trigger-armed' and r['event']['fault']=='timeout']
            require(abs(watchdog['event']['watchdog_deadline_mono']-watchdog['event']['sent_mono']-.25)<1e-6,
                    'watchdog not measured from worker send')
            generation_send, = [r for r in control if r['event']['kind']=='http-sent'
                               and r['event']['worker_sent_mono']==watchdog['event']['sent_mono']]
            timeout, = [r for r in control if r['event']['kind']=='rpc-timeout'
                        and r['event']['pid']==generation_send['event']['pid']]
            require(timeout['mono']>=watchdog['event']['watchdog_deadline_mono'],'watchdog fired before its deadline')
        require(summary['elapsed_seconds']<=plan['caps']['wall'],'formal wall time exceeded')
    final_failure=None
    if failed_final_cleanup:
        latest_start=[r for r in control if r['event']['kind']=='unload-start'][-1]
        latest_stop=[r for r in control if r['event']['kind']=='unload-unverified'][-1]
        start=latest_start['event']
        obs=latest_stop['event']['observation']
        unexpected=[r for r in start['present_before_unload'] if r not in start['old_runners']]
        require(latest_start['seq']<latest_stop['seq'] and unexpected
                and obs['ps']=={'models':[]} and obs['response']['done_reason']=='unload'
                and not any(r['event']['kind']=='dispatch-permit-evaluated' for r in control[latest_start['seq']:]),
                'final cleanup marker evidence incomplete')
        final_failure={'start':latest_start,'stop':latest_stop,'unbound_runner_identities':unexpected,
                       'reason':summary['error'],'service_marker_retained':True}
    return {'acceptance_passed':not failed_final_cleanup,'cases':results,'cleanup_proofs':proofs,'phase_clocks':clocks,
            'final_cleanup_failure':final_failure,'control_counts':charges,'native_immediate_idle_verified':False,
            'real_task_inputs':0}


def inspect_formal_failure(run, artifacts, case_ids=('normal','watchdog','controller','recovery')):
    summary=json.loads((run/'outputs/summary.json').read_bytes())
    driver=run/'outputs/driver'
    control=read_chain(driver/'control.jsonl')
    ledger=read_chain(driver/'campaign/ledger.jsonl')
    require(control[0]['event']['identity']==ledger[0]['event']['binding'],'run journal binding')
    charges=dict.fromkeys(('get','cleanup_get','debug','unload'),0)
    for row in control:
        if row['event']['kind']=='charge':
            charges[row['event']['category']]+=1
    require(charges==summary['control_counts'] and all(v<=summary['caps'][k] for k,v in charges.items()),
            'partial HTTP ledger cap or summary mismatch')
    requests=[r['event'] for r in ledger if r['event']['kind']=='request']
    reserves=summary['reservations']
    require(len(requests)==len(reserves['requests'])<=summary['caps']['requests']
            and sum(r['input'] for r in requests)==reserves['inputs']<=summary['caps']['inputs']
            and sum(r['output'] for r in requests)==reserves['outputs']<=summary['caps']['outputs'],
            'partial dispatch budget or reservation mismatch')
    directory=driver/'campaign/artifacts'
    for row in ledger:
        event=row['event']
        if event['kind']=='bytes':
            data=(directory/event['path']).read_bytes()
            require(len(data)==event['count'] and sha_bytes(data)==event['sha256'],'artifact differs from ledger')
    require(sum(a['size'] for a in artifacts)<=summary['caps']['artifact_bytes']
            and summary['actual_task_inputs']==0,'artifact or data scope exceeded')
    phases=[r['event'] for r in control if r['event']['kind']=='phase-clock']
    started=[r['event']['id'] for r in control if r['event']['kind']=='case-start']
    require(started==list(case_ids[:len(started)]),'partial case order')
    return {'acceptance_passed':False,'failed_prefix_verified':True,'cases_started':started,'cases':summary['cases'],
            'error':summary.get('error'),'phase_clocks':phases,'charges':charges,'reservations':reserves,
            'service_marker_retained':summary['service_marker_retained'],
            'native_immediate_idle_verified':False,'real_task_inputs':0}


def inspect_t2(run, artifacts, status, version):
    stem={'t2':'masbench_t2_live','t2-v2':'masbench_t2_live_v2','t2-v3':'masbench_t2_live_v3'}[version]
    plan_path=f'research/protocols/{stem}_plan.json'
    auth_path=f'research/protocols/{stem}_authorization.json'
    transitions=run/'outputs/service_transitions.jsonl'
    rows=[json.loads(line) for line in transitions.read_bytes().splitlines()] if transitions.exists() else []
    plan=json.loads((ROOT/plan_path).read_bytes())
    if status!='completed':
        result=inspect_formal_failure(run,artifacts,[case['id'] for case in plan['cases']]) if (run/'outputs/summary.json').exists() else {
            'acceptance_passed':False,'summary_available':False}
        return dict(result,service_transitions=rows)
    result=inspect_live(run,artifacts,plan_path,auth_path,formal=True,verify_runner_reuse=True)
    context=plan['runtime']['context']
    require([row['stage'] for row in rows]==['baseline','candidate-profile-written','service-term','service-exited',
            'candidate-first-start','service-term','service-exited','candidate-restart','service-term','service-exited',
            'baseline-restart','rollback-verified'],'unexpected service lifecycle')
    before, first, active, baseline, final = [rows[i] for i in (0,4,7,10,11)]
    services=[row['service'] for row in (before,first,active,baseline)]
    require([item['context'] for item in services]==[1024,context,context,1024]
            and len({(s['service_pid'],s['service_stamp']) for s in services})==4
            and len({s['service_binary_sha256'] for s in services})==1
            and first['profile_exists'] and active['profile_exists'] and not final['profile_exists']
            and final['service']==baseline['service'] and final['empty_runner'] and final['gpu_mib']==0,
            'candidate persistence or baseline rollback evidence missing')
    require(all(rows[i]['service']==service for i,service in zip((3,6,9),services[:3],strict=True)),
            'wrong stopped service identity')
    runtime=json.loads((run/'outputs/summary.json').read_bytes())['runtime']
    require(runtime['service_pid']==active['service']['service_pid']
            and runtime['service_stamp']==active['service']['service_stamp'], 'live campaign ran on wrong service')
    require(result['cases'][0]['reserved_input']>=plan['min_long_prompt_tokens'], 'long case was too short')
    if version=='t2-v3':
        failed=run.parent/'hpc-masbench-t2-live-v2-20261125'
        verify_artifacts(failed)
        old_summary=failed/'outputs/summary.json'
        require(sha_bytes(old_summary.read_bytes())==plan['previous_summary_sha256'],'prior budget identity changed')
        old=json.loads(old_summary.read_bytes())
        driver=failed/'outputs/driver'
        control=read_chain(driver/'control.jsonl')
        ledger=read_chain(driver/'campaign/ledger.jsonl')
        proof,=prove_barriers(control,ledger)
        request,=old['reservations']['requests'].values()
        require(request['status']=='timeout' and request['observed_usage'] is None
                and any(row['event']['kind']=='rpc-timeout' and row['event']['sent_observed'] for row in control)
                and not old['service_marker_retained'],'prior timeout and recovery unverified')
        result['previous_timeout']={'request':request,'cleanup_proof':proof}
    return dict(result,service_transitions=rows,effective_context=context,rollback_verified=True)


def main():
    require_hpc()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('fixture','live','formal','formal-runner-retest','t2','t2-v2','t2-v3'))
    mode = parser.parse_args().mode
    names={'fixture':FIXTURE,'live':LIVE,'formal':'hpc-masbench-t1b-formal-20261119',
           'formal-runner-retest':'hpc-masbench-t1b-formal-runner-retest-20261119','t2':'hpc-masbench-t2-live-20261125',
           't2-v2':'hpc-masbench-t2-live-v2-20261125','t2-v3':'hpc-masbench-t2-live-v3-20261125'}
    run = ROOT/'research/sync/runs'/names[mode]
    status = json.loads((run/'status.json').read_bytes())['status']
    formal = mode in {'formal','formal-runner-retest','t2','t2-v2','t2-v3'}
    require(status=='completed' or formal and status=='failed','source run did not complete')
    artifacts = verify_artifacts(run)
    if mode in {'t2','t2-v2','t2-v3'}:
        result=inspect_t2(run,artifacts,status,mode)
    elif mode=='formal-runner-retest' and status=='completed':
        result=inspect_live(run,artifacts,'research/protocols/masbench_t1b_formal_runner_retest_plan.json',
                            'research/protocols/masbench_t1b_formal_runner_retest_authorization.json',
                            formal=True,verify_runner_reuse=True)
    elif mode=='formal-runner-retest':
        result=inspect_formal_failure(run,artifacts)
    elif mode=='formal':
        summary=json.loads((run/'outputs/summary.json').read_bytes())
        failed_tail=(status=='failed' and len(summary['cases'])==4
                     and summary.get('error')=='SafetyError: old runner identity missing or changed; keep fenced')
        if status=='completed' or failed_tail:
            result=inspect_live(run,artifacts,'research/protocols/masbench_t1b_formal_plan.json',
                                'research/protocols/masbench_t1b_formal_authorization.json',
                                formal=True,failed_final_cleanup=failed_tail)
        else:
            result=inspect_formal_failure(run,artifacts)
    else:
        result = inspect_fixture(run) if mode=='fixture' else inspect_live(run,artifacts)
    write_json(Path(os.environ['GOSC_OUTPUT_DIR'])/'audit.json',
               dict(result,source_run=run.name,artifacts_verified=len(artifacts)))


if __name__=='__main__':
    main()
