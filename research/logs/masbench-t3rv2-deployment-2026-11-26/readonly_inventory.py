"""Bounded administrative inventory, stdout only. Never loads a model.

After the quota gate failed, this independent read-only operation must not be
represented as a registered test or a successful deployment.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid() == 8301880 and Path.cwd() == ROOT
start = time.monotonic()
result = {'kind': 'read-only administrative inventory, not test', 'uid': os.getuid(),
          'host': os.uname().nodename, 'model_generations': 0,
          'service_changes': 0, 'helper_invocations': 0, 'http_attempts': []}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def cmd(args, timeout=5):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=timeout, check=False)
    return {'exit_code': p.returncode, 'stdout': p.stdout[:16384].decode(errors='replace'),
            'stderr': p.stderr[:2048].decode(errors='replace')}


result['git_head'] = cmd(['git', 'rev-parse', 'HEAD'])
result['running_or_planned'] = []
for path in (ROOT/'research/sync/runs').glob('*/status.json'):
    value = json.loads(path.read_bytes())
    if value['status'] in ('running', 'planned'):
        result['running_or_planned'].append({'run': path.parent.name, 'status': value['status']})
result['quota'] = cmd([str(ROOT/'.venv/bin/python'),
    'research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py'])
result['cgroup'] = {}
for name in ('cpu/cpu.cfs_quota_us', 'cpu/cpu.cfs_period_us', 'cpuset/cpuset.cpus',
             'memory/memory.limit_in_bytes', 'memory/tasks', 'cpu/tasks', 'devices/devices.list'):
    path = Path('/sys/fs/cgroup')/name
    result['cgroup'][name] = {'exists': path.exists(), 'writable': os.access(path, os.W_OK),
                            'value': path.read_text()[:2048] if path.is_file() else None}

state_path = ROOT/'.local/ollama/service.json'
state = json.loads(state_path.read_bytes())
pid = state['pid']; proc = Path('/proc')/str(pid)
fields = (proc/'stat').read_text().rsplit(') ', 1)[1].split()
exe = (proc/'exe').resolve()
expected_exe = ROOT/'.local/ollama/runtime/0.11.11/bin/ollama'
if exe != expected_exe or proc.stat().st_uid != os.getuid() or fields[0] == 'Z':
    raise RuntimeError('unexpected service identity; no HTTP allowed')
env = dict(item.split(b'=', 1) for item in (proc/'environ').read_bytes().split(b'\0') if b'=' in item)
whitelist = ('OLLAMA_CONTEXT_LENGTH', 'OLLAMA_NUM_PARALLEL', 'OLLAMA_MAX_LOADED_MODELS',
             'OLLAMA_HOST', 'OLLAMA_MODELS', 'OLLAMA_NO_CLOUD')
result['service'] = {'pid': pid, 'start_stamp': fields[19], 'exe_sha256': sha(exe),
                     'env_whitelist': {k: env.get(k.encode(), b'').decode() for k in whitelist},
                     'context_profile_exists': (ROOT/'.local/ollama/context_profile.json').exists(),
                     'recovery_marker_bytes': (ROOT/'.local/t1-service.lock').stat().st_size}
result['listener'] = cmd(['ss', '-Hlnpt', 'sport = :11434'])
result['connections'] = cmd(['ss', '-Hnt', 'state', 'established', 'sport = :11434 or dport = :11434'])
models = ROOT.parents[1]/'models/ollama-gosc'
result['small_identity_files'] = []
for path in [Path('/tmp/gosc-hpc-masbench-context-build-v3-20261116/context-counter'),
             models/'manifests/registry.ollama.ai/library/qwen2.5/7b',
             models/'blobs/sha256-eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175',
             models/'blobs/sha256-66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e']:
    result['small_identity_files'].append({'path': str(path), 'bytes': path.stat().st_size,
                                          'sha256': sha(path)})
weight = models/'blobs/sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730'
result['model_weight'] = {'path': str(weight), 'bytes': weight.stat().st_size,
                         'sha256_rescanned': False, 'tensor_context_created': False}
result['gpu_observation'] = cmd(['nvidia-smi', '--query-gpu=memory.total,memory.used',
                                '--format=csv,noheader,nounits'])
# Exactly three no-retry GETs, after verifying the owned listener process.
if env.get(b'OLLAMA_HOST') == b'127.0.0.1:11434' and f'pid={pid},' in result['listener']['stdout']:
    for path in ('/api/version', '/api/ps', '/api/tags'):
        row = {'method': 'GET', 'path': path, 'attempt': 1}
        result['http_attempts'].append(row)
        c = http.client.HTTPConnection('127.0.0.1', 11434, timeout=3)
        try:
            c.request('GET', path)
            response = c.getresponse(); body = response.read(65537)
            if response.status != 200 or len(body) > 65536:
                raise RuntimeError('metadata HTTP status/size')
            row.update(status=response.status, response=json.loads(body),
                       response_sha256=hashlib.sha256(body).hexdigest())
        except Exception as exc:
            row['error_type'] = type(exc).__name__
            break
        finally:
            c.close()
result['elapsed_seconds'] = time.monotonic()-start
print(json.dumps(result, ensure_ascii=False, sort_keys=True))
