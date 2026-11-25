"""Offline score and independently reconcile the sealed T3 HDD run."""
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'scripts')]
from hpc_runs import require_hpc, write_json
from experiments_ext import masbench_t2_window_demand as data
from experiments_ext.masbench_t1a_contract import deny_network
from experiments_ext.masbench_t1a_evidence_audit import read_chain
from extensions.masbench_reasoning import live_driver as live
from extensions.masbench_reasoning.evaluation import summarize
from extensions.masbench_reasoning.execution_safety import SafetyError,digest


def read_json(path):
    return json.loads(path.read_bytes())


def audit(run):
    auth = read_json(ROOT/live.T3_AUTH)
    if auth['run_id']!=run.name or live.file_sha(ROOT/live.T3_PLAN)!=auth['plan_sha256']:
        raise SafetyError('frozen run identity mismatch')
    index = read_json(run/'outputs/hdd_manifest.json')
    summary = read_json(run/'outputs/live_summary.json')
    root = live.reject_links(live.T3_EVIDENCE_ROOT/run.name)
    if index['hdd_root']!=str(root) or not index['readback_verified'] or index['raw_mirrored']:
        raise SafetyError('HDD evidence pointer mismatch')
    present = {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
    listed = {row['path']:row for row in index['files']}
    if (set(present)!=set(listed) or len(set(listed))!=len(index['files'])
            or sum(row['size'] for row in listed.values())!=index['bytes'] or index['bytes']>live.T3_HDD_BYTES):
        raise SafetyError('HDD inventory mismatch')
    for name,path in present.items():
        if path.is_symlink() or path.stat().st_size!=listed[name]['size'] or live.file_sha(path)!=listed[name]['sha256']:
            raise SafetyError('sealed HDD file changed')
    result = {'registered_status':read_json(run/'status.json')['status'],'live_status':summary['status'],
              'failure':summary['failure'],'hdd_bytes':index['bytes'],'hdd_files':len(listed),
              'raw_mirrored':False,'raw_hdd_sha256_verified':True}
    if 'live/campaign/ledger.jsonl' not in present:
        return dict(result,science_disposition='incomplete',requests=0,episodes_started=0)
    ledger = read_chain(root/'live/campaign/ledger.jsonl')
    control = read_chain(root/'live/control.jsonl')
    if (ledger[-1]['hash']!=summary['ledger_tip'] or control[-1]['hash']!=summary['control_tip']
            or ledger[0]['event']['binding']!=control[0]['event']['identity']):
        raise SafetyError('ledger/control tips or identity mismatch')

    requests, episodes, outputs, captures, renders, bindings = {}, {}, {}, {}, {}, {}
    providers = defaultdict(list)
    received_wire = {}
    last_wire = None
    barriers = 0
    for row in ledger:
        event = row['event']
        kind = event['kind']
        if kind=='request':
            key = event['id']
            if key in requests or event['input']+event['output']>16384 or event['output']!=512:
                raise SafetyError('duplicate, oversized or unbudgeted request')
            requests[key] = dict(event)
        elif kind=='finish':
            key = event['id']
            if requests[key]['status']!='inflight':
                raise SafetyError('duplicate usage settlement')
            usage = event['usage']
            if usage is not None and (usage['prompt_tokens']!=requests[key]['input']
                                       or not 0<=usage['completion_tokens']<=512):
                raise SafetyError('known usage conflicts with reservation')
            requests[key].update(status=event['status'],observed_usage=usage)
        elif kind=='episode':
            key = event['id']
            if event['status']=='started' and key in episodes:
                raise SafetyError('episode replay')
            episodes[key]=event['status']
        elif kind=='barrier':
            barrier = control[event['receipt']['control_event_seq']]
            observation = barrier['event']['observation']
            if (barrier['hash']!=event['receipt']['control_event_hash']
                    or barrier['event']['kind']!='unload-complete'
                    or not observation['process_observations']
                    or observation['ps']['models'] or observation['remaining_runners']
                    or any(x['stamp']==x['observed_stamp'] for x in observation['process_observations'])):
                raise SafetyError('missing exit witness behind recovery barrier')
            barriers += 1
        elif kind=='bytes':
            artifact = 'live/campaign/artifacts/'+event['path']
            recorded = listed.get(artifact)
            if not recorded or recorded['sha256']!=event['sha256'] or recorded['size']!=event['count']:
                raise SafetyError('missing HDD ledger artifact')
            if artifact.endswith('-full-input-count.json'):
                value = read_json(present[artifact])
                renders[digest(value['messages'])]=value['row']
            elif artifact.endswith('-binding-evidence.json'):
                value = read_json(present[artifact])
                bindings[value['input_sha']]=value
            elif artifact.endswith('-provider-request.json'):
                value = read_json(present[artifact])
                key,episode = value['request_id'],value['episode_id']
                if key not in requests or key in captures or requests[key]['episode']!=episode:
                    raise SafetyError('provider request was not reserved against this episode')
                payload = value['payload']
                input_hash = digest(payload['messages'])
                counted,binding = renders[input_hash],bindings[input_hash]
                active = binding['ps']['models']
                if (counted['token_count']!=requests[key]['input'] or payload['max_tokens']!=512
                        or counted['rendered']!=binding['debug']['_debug_info']['rendered_template']
                        or len(active)!=1 or active[0]['digest']!=live.MANIFEST
                        or active[0]['context_length']!=16384):
                    raise SafetyError('provider request diverges from exact context evidence')
                captures[key] = digest(payload)
                providers[episode].append(payload['messages'])
            elif artifact.endswith('-wire-events.json'):
                last_wire = read_json(present[artifact])
            elif artifact.endswith('-application-result.json'):
                value = read_json(present[artifact])
                key = value['id']
                if key in outputs or last_wire is None:
                    raise SafetyError('application result repeated or lacks wire record')
                outputs[key],received_wire[key] = value,last_wire
                last_wire = None

    control_events = [row['event'] for row in control]
    charges = Counter(event['category'] for event in control_events if event['kind']=='charge')
    dispositions = {event['request_id']:event for event in control_events if event['kind']=='runner-dispatch-bound'}
    if any(dispositions[k]['payload_sha256']!=v for k,v in captures.items()):
        raise SafetyError('provider payload differs from runner-bound payload')
    if (set(charges)-set(live.T3_CONTROL) or {k:charges[k] for k in live.T3_CONTROL}!=summary['control_counts']
            or any(charges[k]>cap for k,cap in live.T3_CONTROL.items())):
        raise SafetyError('management charges do not reconcile')
    plan = read_json(ROOT/live.T3_PLAN)['episodes']
    ordered = [r['id'] for r in plan]
    planned = ['synthetic-short','synthetic-long']+ordered
    if list(episodes)!=planned[:len(episodes)] or (set(episodes)-set(planned)):
        raise SafetyError('episode identity/order changed')
    reservations = Counter(r['episode'] for r in requests.values())
    partition_use = Counter(k.split('/')[0] for k in requests)
    inputs = sum(r['input'] for r in requests.values())
    outputs_reserved = sum(r['output'] for r in requests.values())
    if (partition_use['task']>96 or partition_use['synthetic']>2
            or inputs>1555456 or outputs_reserved>50176
            or any(reservations[k]>(1 if k.startswith('synthetic-') else 6) for k in episodes)
            or requests!=summary['requests']):
        raise SafetyError('partition, final state or cumulative budget did not reconcile')
    if any(k.split('/')[0]!=('synthetic' if r['episode'].startswith('synthetic-') else 'task')
           for k,r in requests.items()):
        raise SafetyError('request charged to wrong partition')
    transitions = [json.loads(line) for line in (root/'service_transitions.jsonl').read_bytes().splitlines()]
    rolled_back = bool(transitions and transitions[-1]['stage']=='rollback-verified')
    complete = (result['registered_status']=='completed' and result['live_status']=='completed' and rolled_back
                and len(episodes)==18 and barriers==18 and set(captures)==set(requests)
                and all(r['status']!='inflight' for r in requests.values()))

    # Gold is first read here, after the registered live run is terminal.
    selected, items, _ = data.development_inputs()
    scored = {}
    evidence_rows = []
    for row in plan:
        key = row['id']
        if key not in episodes:
            continue
        gold = items[selected[row['case']-1]['row']]['answer']
        outcome = outputs.get(key,{})
        reason = outcome.get('end_reason','model_error')
        answer = outcome.get('final_answer')
        record = {'id':key,'gold':gold,'answer':answer,'end_reason':reason}
        scored[key] = record
        quality = summarize([key],[record])
        next_requests = providers[key][1:]
        delivered = []
        for turn,message in enumerate(outcome.get('messages',[])[:len(next_requests)]):
            if not message['delivered'] or message['visible'] is None:
                continue
            body = bytes.fromhex(message['body']['utf8_or_wire_hex'])
            if hashlib.sha256(body).hexdigest()!=message['payload_sha256']:
                raise SafetyError('message payload changed')
            request = next_requests[turn]
            if any(m['role']=='user' and m['content'].startswith(body.decode()) for m in request[1:]):
                delivered.append({'turn':turn+1,'payload_sha256':message['payload_sha256'],
                                  'receiver_request_sha256':data.digest(request)})
        if row['condition']=='No-A2A' and (delivered or any(m['delivered'] for m in outcome.get('messages',[]))):
            raise SafetyError('No-A2A communication isolation failed')
        frames = [event for event in received_wire.get(key,{}).get('events',[]) if event['event']=='frame']
        evidence_rows.append({'id':key,'end_reason':reason,'EM':quality['EM_all_added'],'F1':quality['mean_F1_all'],
                              'requests':reservations[key],'receiver_next_requests':delivered,
                              'wire_bytes':sum(x['bytes'] for x in frames),
                              'channel_uses':sum(x['uses'] for x in frames)})
    scores = {row['id']:row for row in evidence_rows}
    primary = [row for row in plan if row['style']=='base' and row['condition']=='Full']
    family_correct = {row['family_sha256'] for row in primary if scores.get(row['id'],{}).get('EM')==1}
    pairs = []
    for row in plan:
        if row['condition']!='Full':
            continue
        key = row['id']
        peer = key.removesuffix('Full')+'No-A2A'
        if key in scores and peer in scores:
            pairs.append({'full':key,'no_a2a':peer,'style':row['style'],
                          'F1_difference':scores[key]['F1']-scores[peer]['F1'],
                          'full_has_receiver_request':bool(scores[key]['receiver_next_requests'])})
    effect = any(row['style']=='base' and row['F1_difference']>0 and row['full_has_receiver_request'] for row in pairs)
    unknown = [r for r in requests.values() if r.get('observed_usage') is None]
    return dict(result,
        science_disposition=('go' if len(family_correct)>=2 and effect else 'no_go') if complete else 'incomplete',
        engineering_complete=complete,rollback_verified=rolled_back,old_runner_barriers=barriers,
        requests=len(requests),partition_use=dict(partition_use),inputs_reserved=inputs,outputs_reserved=outputs_reserved,
        unknown_requests=[r['id'] for r in unknown],unknown_reserved_inputs=sum(r['input'] for r in unknown),
        unknown_reserved_outputs=sum(r['output'] for r in unknown),
        known_prompt_tokens=sum(r['observed_usage']['prompt_tokens'] for r in requests.values() if r not in unknown),
        known_completion_tokens=sum(r['observed_usage']['completion_tokens'] for r in requests.values() if r not in unknown),
        full_correct_families_base=len(family_correct),base_positive_delivery_pair=effect,
        scopes={f'{style}/{condition}':summarize(
            [r['id'] for r in plan if r['style']==style and r['condition']==condition],
            [scored[r['id']] for r in plan if r['style']==style and r['condition']==condition and r['id'] in scored])
            for style in data.FAMILIES for condition in ('Full','No-A2A')},
        episodes=evidence_rows,pairs=pairs,resource_peaks=summary['resource_peaks'])


def main():
    require_hpc()
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    deny_network()
    auth = read_json(ROOT/live.T3_AUTH)
    run = ROOT/'research/sync/runs'/auth['run_id']
    if read_json(run/'status.json')['status'] not in {'completed','failed','interrupted'}:
        raise SafetyError('audit requires terminal registered run')
    result = audit(run)
    write_json(Path(os.environ['GOSC_OUTPUT_DIR'])/'t3_audit.json',result)
    print(json.dumps({k:result[k] for k in ('live_status','science_disposition','requests','hdd_bytes')}))


if __name__=='__main__':
    main()
