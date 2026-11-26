"""HPC-only offline preflight for the four previously exposed T3 families."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import time

from scripts.hpc_runs import require_hpc, resource_limits, write_json
from experiments_ext.masbench_t1b_live import own_listener
from experiments_ext.masbench_t3rv2_live_probe import quota, storage_gate
from extensions.masbench_reasoning import fair_final_v2_task as task, live_driver as live
from extensions.masbench_reasoning.application import PrivateView
from extensions.masbench_reasoning.execution_safety import SafetyError, canonical, digest
from extensions.masbench_reasoning.fair_final_v2_task_campaign import preflight_initial_inputs

TRACE = task.ROOT / 'research/logs/masbench-t3r-2026-11-25/episode_trace_index.json'
HISTORICAL = Path('/hdd/u202520081000097/gosc-t3-runs/hpc-masbench-t3-live-20261125')
PRIVATE = Path('/hdd/u202520081000097/gosc-t3rv2t-admission')
PROMPT = re.compile(r"You are (Alice|Bob), collaborating with (Alice|Bob) to answer a multi-hop question using the private information given below\.\n\nQuestion: (.*?)\n\nInformation \(only visible to you\):\n(.*?)\n\nTASK:\n", re.S)


def historical_views(plan):
    index = json.loads(TRACE.read_bytes())
    if Path(index['hdd_root']) != HISTORICAL:
        raise SafetyError('historical_root_mismatch')
    output = []
    for row in plan[::2]:
        episode, = (e for e in index['episodes'] if e['family_sha256'] == row['family']
                    and e['style'] == 'protocol' and e['condition'] == 'No-A2A')
        views = []
        for turn, role in enumerate(('Alice', 'Bob')):
            evidence = episode['turns'][turn]
            source = evidence['provider_source']
            path = live.reject_links(HISTORICAL / source['path'])
            if HISTORICAL not in path.parents or evidence['speaker'] != role or path.stat().st_size > 512 * 1024:
                raise SafetyError('historical_request_scope')
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME), 'rb') as stream:
                raw = stream.read()
            if hashlib.sha256(raw).hexdigest() != source['file_sha256']:
                raise SafetyError('historical_request_drift')
            messages = json.loads(raw)['payload']['messages']
            if len(messages) != 1 or messages[0]['role'] != 'system':
                raise SafetyError('historical_request_was_not_local_initial')
            match = PROMPT.match(messages[0]['content'])
            if not match or match[1] != role or match[2] == role:
                raise SafetyError('historical_local_view_shape')
            views.append(asdict(PrivateView(*match.groups())))
        if digest(views) != row['private_view_sha256']:
            raise SafetyError('historical_pair_sha_mismatch')
        output.append(dict(family=row['family'], views=views))
    return dict(schema='four-local-views-v1', families=output)


def site():
    limits = resource_limits()
    if (int(limits['cpu_quota']) != 2 * int(limits['cpu_period'])
            or int(limits['memory_bytes']) != 24 * 1024**3):
        raise SafetyError('site_cgroup_drift')
    quotas = quota()
    storage_gate(quotas)
    if quotas['volumes']['hdd']['remaining_to_hard_limit_bytes'] < 2 * 1024**3:
        raise SafetyError('HDD_headroom')
    pid = json.loads((task.ROOT / '.local/ollama/service.json').read_bytes())['pid']
    runtime = live.Runtime(str(task.ROOT), task.HELPER, pid, live.proc_stamp(pid), task.BINARY_SHA, 1024)
    models = live.runtime_files(runtime)
    own_listener(runtime)
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], timeout=3)
    if (gpu.split() != [b'0'] or live.runner_identities(runtime)
            or (task.ROOT / '.local/ollama/context_profile.json').exists()
            or (task.ROOT / '.local/t1-service.lock').stat().st_size):
        raise SafetyError('site_not_idle')
    return runtime, models, quotas, limits


def main():
    require_hpc()
    os.umask(0o077)
    os.environ.update(CUDA_VISIBLE_DEVICES='', GOMAXPROCS='2')
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    start = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('admission_360s')))
    signal.alarm(360)
    run = Path(os.environ['GOSC_RUN_DIR'])
    output = Path(os.environ['GOSC_OUTPUT_DIR'])
    if not run.name.startswith('hpc-t3rv2i-task-admission-'):
        raise SafetyError('registered_admission_required')
    runtime, models, quotas, limits = site()
    plan = json.loads(task.PLAN.read_bytes())['episodes']
    task.validate_plan(plan)
    bundle = canonical(historical_views(plan))
    private = live.reject_links(PRIVATE / run.name)
    private.mkdir(parents=True, mode=0o700, exist_ok=False)
    bundle_path = private / 'views.json'
    bundle_path.write_bytes(bundle)
    bundle_sha = hashlib.sha256(bundle).hexdigest()
    views = task.load_private_bundle(bundle_path, bundle_sha, plan)
    weight = models / 'blobs' / live.MODEL_BLOB
    sha_started = time.monotonic()
    hasher = hashlib.sha256()
    with weight.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024**2), b''):
            hasher.update(chunk)
            if time.monotonic() - sha_started > 120:
                raise TimeoutError('weight_check_120s')
    if hasher.hexdigest() != live.MODEL_BLOB.removeprefix('sha256-'):
        raise SafetyError('weight_sha_mismatch')
    counter_calls = 0

    def counter(messages):
        nonlocal counter_calls
        counter_calls += 1
        if counter_calls > 8:
            raise SafetyError('offline_counter_cap')
        data = canonical(dict(model_path=str(weight), template_path=str(models / 'blobs' / ('sha256-' + live.TEMPLATE)),
                              template_sha256=live.TEMPLATE, requests=[dict(messages=messages)], texts=[]))
        raw = subprocess.run([task.HELPER], input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             timeout=20, check=True).stdout
        if len(raw) > 768 * 1024:
            raise SafetyError('offline_counter_reply_cap')
        reply = json.loads(raw)
        input_sha = hashlib.sha256(data).hexdigest()
        if reply.get('input_sha256') != input_sha:
            raise SafetyError('offline_counter_input_mismatch')
        row = task.verify_count(messages, reply)
        (private / f'counter-{counter_calls}.json').write_bytes(raw)
        return dict(request_sha256=digest(messages), tokens=row['token_count'], request_bytes=len(canonical(messages)),
                    rendered_sha256=row['rendered_sha256'], token_ids_sha256=row['token_ids_json_sha256'])

    # Retain each successful row even if a subsequent bounded count fails.
    rows_path = private / 'counts.jsonl'
    with rows_path.open('xb') as stream:
        def record(row):
            stream.write(canonical(row) + b'\n')
            stream.flush()
        rows = preflight_initial_inputs(plan, views, counter, record)
    after, _, _, _ = site()
    if after != runtime or len(rows) != 8:
        raise SafetyError('site_or_count_drift')
    report = dict(passed=True, run_id=run.name, view_bundle_path=str(bundle_path), view_bundle_sha256=bundle_sha,
                  view_count=8, counts=rows, helper_calls=counter_calls, model_calls=0, service_http_calls=0,
                  baseline_pid=runtime.service_pid, baseline_stamp=runtime.service_stamp, baseline_context=1024,
                  binary_sha256=task.BINARY_SHA, helper_sha256=live.HELPER_SHA, model_manifest_sha256=live.MANIFEST,
                  weight_sha256=hasher.hexdigest(), template_sha256=live.TEMPLATE,
                  plan_sha256=digest(plan), historical_index_sha256=live.file_sha(TRACE),
                  quotas=quotas, limits=limits, elapsed_seconds=time.monotonic()-start)
    write_json(output / 'admission.json', report)
    print(json.dumps(dict(counts=len(rows), max_input_tokens=max(row['tokens'] for row in rows), model_calls=0)))


if __name__ == '__main__':
    main()
