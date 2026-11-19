"""Read-only independent audit of a registered T1-A run. No Driver imports."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hpc_runs import require_hpc, write_json


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                allow_nan=False).encode())


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_chain(path):
    data = path.read_bytes().rstrip(b'\0')
    rows = []
    tip = '0' * 64
    for line in data.splitlines(keepends=True):
        row = json.loads(line)
        fingerprint = row.pop('hash')
        require(line.endswith(b'\n') and row['seq'] == len(rows) and row['previous'] == tip
                and canonical_sha(row) == fingerprint, f'invalid hash chain {path}')
        rows.append(dict(row, hash=fingerprint))
        tip = fingerprint
    require(rows and rows[0]['event']['kind'] == 'init', 'missing journal header')
    return rows


def inspect_campaign(directory):
    ledger = read_chain(directory / 'campaign/ledger.jsonl')
    control = read_chain(directory / 'control.jsonl')
    require(control[0]['event']['identity'] == ledger[0]['event']['binding'], 'ledger/control identity mismatch')
    usage = {}
    charges = {}
    requests = {}
    barriers = 0
    for row in ledger:
        event = row['event']
        kind = event['kind']
        if kind == 'bytes':
            path = directory / 'campaign/artifacts' / event['path']
            data = path.read_bytes()
            require(len(data) == event['count'] and sha_bytes(data) == event['sha256'], 'artifact mismatch')
        elif kind == 'request':
            require(event['id'] not in requests, 'duplicate request ID')
            requests[event['id']] = event
        elif kind == 'finish':
            require(event['id'] in requests and event['id'] not in usage, 'unreserved or duplicate settlement')
            if event['status'] != 'completed':
                require(event['usage'] is None, 'failed usage fabricated')
            usage[event['id']] = event
        elif kind == 'barrier':
            receipt = event['receipt']
            proof = control[receipt['control_event_seq']]
            require(proof['hash'] == receipt['control_event_hash'], 'unbound recovery receipt')
            observation = proof['event']['observation']
            require(proof['event']['kind'] == 'unload-complete'
                    and observation['ledger_seq'] == row['seq']
                    and observation['ledger_tip'] == row['previous']
                    and observation['ps']['models'] == []
                    and observation['response']['done_reason'] == 'unload'
                    and observation['response']['done'] is True
                    and all(item['stamp'] != item['observed_stamp'] for item in observation['process_observations']),
                    'recovery proof does not match current ledger and observations')
            barriers += 1
    for row in control:
        event = row['event']
        if event['kind'] == 'charge':
            category = event['category']
            charges[category] = charges.get(category, 0) + 1
        require(event['kind'] != 'http-sent', 'unexpected actual HTTP send')
    caps = control[0]['event']['caps']
    require(all(value <= caps[key] for key, value in charges.items()), 'control quota exceeded')
    return {
        'ledger_events': len(ledger), 'control_events': len(control), 'requests': len(requests),
        'reserved_input': sum(x['input'] for x in requests.values()),
        'reserved_output': sum(x['output'] for x in requests.values()),
        'unknown_usage': [x['id'] for x in usage.values() if x['usage'] is None],
        'barriers': barriers, 'charges': charges,
    }, control


def main():
    require_hpc()
    if len(sys.argv) != 2 or not re.fullmatch(r'hpc-masbench-t1a-contract-v[0-9]+-20261118', sys.argv[1]):
        raise RuntimeError('explicit T1-A source run required')
    run = ROOT / 'research/sync/runs' / sys.argv[1]
    require(json.loads((run / 'status.json').read_bytes())['status'] == 'completed', 'source run not completed')
    stderr = (run / 'stderr.log').read_text()
    require(re.search(r'Ran [0-9]+ tests.*\n\nOK\s*$', stderr), 'fixture suite did not finish green')
    artifacts = json.loads((run / 'artifacts.json').read_bytes())['files']
    for a in artifacts:
        data = (run / a['path']).read_bytes()
        require(len(data) == a['size'] and sha_bytes(data) == a['sha256'], f'run artifact drift: {a["path"]}')

    selected = [
        'test_paid_worker_timeout_then_cleanup_and_resumed_dispatch',
        'test_interrupted_inflight_keeps_unknown_cost_and_requires_cleanup',
        'test_unload_failure_keeps_fence',
        'test_application_base_delivery',
        'test_application_protocol_delivery',
        'test_other_campaign_cannot_bypass_recovery_after_close',
    ]
    report = {}
    for name in selected:
        directory = run / 'outputs/fixtures' / name / 'driver'
        result, control = inspect_campaign(directory)
        if name == selected[0]:
            kinds = [row['event']['kind'] for row in control]
            sequence = [kinds.index(k) for k in ['fixture-send-marker','rpc-timeout','client-failure',
                                                 'unload-start','unload-complete','dispatch-permit-evaluated']]
            require(sequence == sorted(sequence) and len(set(sequence)) == len(sequence), 'timeout/cleanup event order')
            signals = [r['event'] for r in control[sequence[1]+1:sequence[2]]
                       if r['event']['kind'] == 'signal' and r['event']['sent']]
            require(any(e['signal'] == 9 for e in signals), 'actual owned-worker SIGKILL missing')
            require(result['reserved_output'] == 16 and result['unknown_usage'] == ['synthetic/0'], 'timeout refund/unknown mismatch')
        if name == selected[1]:
            require(result['reserved_input'] == 25 and result['reserved_output'] == 16
                    and result['unknown_usage'] == ['synthetic/0'], 'interruption reservation mismatch')
        if name == selected[2]:
            require(result['barriers'] == 0 and result['unknown_usage'] == ['synthetic/0'], 'unload failure cleared fence')
        if name in selected[3:5]:
            files = sorted((directory / 'campaign/artifacts').glob('*-application-result.json'))
            full, none = [json.loads(path.read_bytes()) for path in files]
            require(full['messages'][0]['delivered'] and not none['messages'][0]['delivered'], 'application delivery mismatch')
            require(result['requests'] == 4 and result['reserved_output'] == 32, 'application accounting mismatch')
        report[name] = result
    write_json(Path(os.environ['GOSC_OUTPUT_DIR']) / 'audit.json', {
        'source_run': sys.argv[1], 'artifacts_verified': len(artifacts), 'campaigns': report,
        'live_service_requests': 0, 'real_task_inputs': 0, 'native_immediate_idle_verified': False,
    })


if __name__ == '__main__':
    main()
