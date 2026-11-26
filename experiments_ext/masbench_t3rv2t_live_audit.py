"""Independent live audit. It uses evidence bytes, never the driver or scorer."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import time

from experiments_ext.masbench_t3rv2t_admission_paths import LIVE_ID, LIVE_HDD

CAPS = dict(generation=48, render=48, get=152, cleanup_get=56, unload=8, lifecycle_get=128)
MANIFEST = '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'


def need(test, code):
    if not test:
        raise ValueError(code)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded(value, ascii=True):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False, ensure_ascii=ascii).encode()


def digest(value, ascii=True):
    return hashlib.sha256(encoded(value, ascii)).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def inventory(root, rows):
    need(root.is_dir() and not root.is_symlink(), 'HDD_root')
    expected = {row['path']: row for row in rows}
    found = {}
    for path in root.rglob('*'):
        need(not path.is_symlink() and (path.is_file() or path.is_dir()), 'HDD_file_type')
        if path.is_file():
            found[path.relative_to(root).as_posix()] = path
    need(len(expected) == len(rows) and found.keys() == expected.keys(), 'HDD_file_set')
    total = sum(path.stat().st_size for path in found.values())
    need(total <= 1024**3, 'HDD_bytes_cap')
    for key, path in found.items():
        need(path.stat().st_size == expected[key]['bytes'] and sha(path) == expected[key]['sha256'], 'HDD_file_binding')
    return total


def journal(path):
    previous = '0' * 64
    with path.open('rb') as stream:
        for seq, line in enumerate(stream):
            row = json.loads(line)
            tip = row.pop('hash')
            need(row['seq'] == seq and row['previous'] == previous and digest(row) == tip, 'journal_chain')
            previous = tip
            yield row['event']


def verify_slot(art, episode, slot, reservation, finish):
    path = art / episode / f"t{slot['turn']}"
    precount, binding = (read(path / name) for name in ('count.json', 'binding.json'))
    ready = read(path / 'client-request_ready.json')['data']
    done = read(path / 'client-completed.json')['data']
    request = slot['request']
    reply = precount['reply']
    count, = reply['requests']
    ids, rendered = count['token_ids'], count['rendered']
    need(reply['vocab_only'] is True and reply['tensor_context_created'] is False
         and reply['template_sha256'] == 'eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175'
         and reply['add_special'] is False and reply['parse_special'] is True
         and len(ids) == count['token_count'] <= 15872 and digest(ids) == count['token_ids_json_sha256']
         and hashlib.sha256(rendered.encode()).hexdigest() == count['rendered_sha256'], 'exact_count')
    model, = binding['ps']['models']
    need(binding['debug']['_debug_info']['rendered_template'] == rendered
         and model['digest'] == MANIFEST and model['context_length'] == 16384
         and binding['version']['version'] == '0.11.11' and binding['messages_sha256'] == digest(request), 'runtime_binding')
    need(request == ready['messages'] == precount['messages'] and slot['request_sha256'] == digest(request, False)
         and ready['request_sha256'] == digest(request, False), 'request_binding')
    usage = done['usage']
    need(done['error'] is None and not done['usage_missing'] and done['finish_reason'] == 'stop'
         and done['response']['model'] == 'qwen2.5:7b' and done['response_sha256'] == digest(done['response'], False)
         and slot['raw'] == done['response']['choices'][0]['message']['content']
         and count['token_count'] == ready['prompt_tokens_preflight'] == usage['prompt_tokens'] == reservation['input']
         and reservation['output'] == 512 and usage['completion_tokens'] <= 512
         and finish['status'] == 'completed' and finish['uncertain'] is False
         and finish['usage'] == {key: usage[key] for key in ('prompt_tokens', 'completion_tokens')}, 'usage_binding')


def audit(run, root, plan):
    outputs = run / 'outputs'
    listing = read(outputs / 'hdd_inventory.json')
    need(Path(listing['root']) == root, 'HDD_inventory_root')
    bytes_checked = inventory(root, listing['files'])
    manifest, terminal = read(run / 'manifest.json'), read(run / 'status.json')
    summary = read(outputs / 'task_summary.json')
    auth = read(root / 'authorization.json')
    need(auth['approved'] is True and auth['run_id'] == manifest['run_id'] == run.name
         and auth['git_commit'] == manifest['git_commit'] and auth['plan_sha256'] == digest(plan), 'frozen_run_identity')
    snapshot = run / 'source_snapshot.json'
    need(sha(snapshot) == manifest['source_manifest_sha256'], 'snapshot_SHA')
    file_pins = {row['path']: row['remote_sha256'] for row in read(snapshot)['files']}
    need(all(file_pins.get(name) == pin for name, pin in auth['bound_files'].items()), 'snapshot_source_pins')
    need(terminal['status'] == 'completed' and summary['execution_and_rollback_passed'], 'execution_incomplete')
    art = root / 'budget/artifacts'
    reservations, finished, sent, cleanup, episodes = {}, {}, set(), {}, []
    http, ops = Counter(), Counter()
    exits = []
    previous = None
    active_samples = 0
    rollback = None
    started = None
    for event in journal(root / 'budget/ledger.jsonl'):
        kind = event['kind']
        if kind == 'init':
            started = event['started_utc']
        elif kind == 'request':
            need(event['id'] not in reservations, 'duplicate_reservation')
            reservations[event['id']] = event
        elif kind == 'finish':
            need(event['id'] in sent and event['id'] not in finished, 'finish_without_unique_send')
            finished[event['id']] = event
        elif kind == 'v2-http':
            need(event['fake_operation'] is False and event['category'] in CAPS, 'live_http_category')
            http[event['category']] += 1
            if event['category'] == 'generation':
                rid = event['request_id']
                need(rid in reservations and rid not in sent, 'generation_reservation')
                sent.add(rid)
        elif kind == 'task-operation':
            ops[event['name']] += 1
        elif kind == 'episode' and event['status'] == 'completed':
            episodes.append(event['id'])
        elif kind == 'cleanup':
            cleanup[event['episode']] = event['status']
        elif kind == 'bytes':
            match = next((row for row in listing['files'] if row['path'] == 'budget/artifacts/' + event['path']), None)
            need(match and match['sha256'] == event['sha256'] and match['bytes'] == event['count'], 'journal_artifact_binding')
        elif kind == 'v2-fence':
            raise ValueError('persistent_fence')
        elif kind == 'task-control':
            label = event['label']
            if label == 'monitor-bind':
                previous = None
            elif label == 'resources':
                values = event['values']
                need(all(0 <= values[key] <= cap * 1024**3 for key, cap in
                         [('driver_rss', 2), ('service_rss', 16), ('gpu_bytes', 16)]), 'resource_limit')
                if event['enforced_active']:
                    now = event['sample_start']
                    need(previous is None or 0 <= now - previous <= .5, 'resource_sample_gap')
                    previous = now
                    active_samples += 1
            elif label == 'exit-barrier':
                need(event['ps']['models'] == [] and event['remaining'] == [] and event['old']
                     and all(row['observed_stamp'] != row['stamp'] for row in event['process_observations']), 'runner_exit')
                exits.append(event['episode'])
            elif label == 'rollback-verified':
                need(rollback is None and event['lease_bytes'] == 0 and not event['profile_exists'], 'rollback_marker')
                rollback = event['runtime']
    ids = [row['id'] for row in plan]
    need(episodes == exits == ids and cleanup == dict.fromkeys(ids, 'verified'), 'episode_cleanup')
    need(rollback and rollback['context'] == 1024 and rollback == summary['restored'] and active_samples > 0, 'rollback_and_monitor')
    expected = {f'{episode}/t{turn}' for episode in ids for turn in range(6)}
    need(expected == reservations.keys() == finished.keys() == sent, 'exact_dispatch_set')
    need(all(http[key] == summary['http'][key] <= CAPS[key] for key in CAPS)
         and (http['generation'], http['render'], http['unload']) == (48, 48, 8)
         and dict(ops) == summary['operations'] == dict(counter=48, precount=8, start=2, stop=2), 'metered_totals')
    for row in plan:
        episode = read(art / 'episodes' / (row['id'] + '.json'))
        need(episode['id'] == row['id'] and episode['condition'] == row['condition'] and episode['completed']
             and [slot['turn'] for slot in episode['slots']] == list(range(6)), 'episode_slot_order')
        for slot in episode['slots']:
            rid = f"{row['id']}/t{slot['turn']}"
            verify_slot(art, row['id'], slot, reservations[rid], finished[rid])
    return dict(passed=True, runtime_bound=True, resource_monitor_passed=True, rollback_verified=True,
                ledger_started_utc=started, task_requests=len(sent), hdd_bytes=bytes_checked,
                inventory_sha256=sha(outputs / 'hdd_inventory.json'))


def main():
    from scripts.hpc_runs import ROOT, require_hpc, write_json
    require_hpc()
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3,) * 2)
    out = Path(os.environ['GOSC_OUTPUT_DIR'])
    run = ROOT / 'research/sync/runs' / LIVE_ID
    plan = read(ROOT / 'research/protocols/masbench_t3rv2t_plan_2026-11-26.json')['episodes']
    start = time.monotonic()
    try:
        report = audit(run, LIVE_HDD / LIVE_ID, plan)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        report = dict(passed=False, error=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
    write_json(out / 'live_audit.json', dict(report, run_id=LIVE_ID, audit_seconds=time.monotonic() - start))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
