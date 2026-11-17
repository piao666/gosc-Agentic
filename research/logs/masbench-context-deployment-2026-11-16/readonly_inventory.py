"""Read-only SSH preflight; no weights, task data, installs or HTTP POST."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request

root = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid() == 8301880 and root.is_dir()

def cmd(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
    return {'exit': p.returncode, 'stdout': p.stdout.decode(errors='replace').strip(),
            'stderr': p.stderr.decode(errors='replace')[:600]}

result = {'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'uid': os.getuid(), 'root': str(root), 'no_generation': True,
          'git_head': cmd(['git', '-C', str(root), 'rev-parse', 'HEAD']),
          'git_branch': cmd(['git', '-C', str(root), 'symbolic-ref', '--short', 'HEAD']),
          'git_origin': cmd(['git', '-C', str(root), 'remote', 'get-url', 'origin']),
          'git_objects_current_archive': cmd(['git', '-C', str(root), 'cat-file', '-t',
                                             '916289ba20fd9808a3673af0aebf175bfc830ccc']),
          'tools': {x: shutil.which(x) for x in ['go','gcc','g++','cmake','lfs','quota','timeout','prlimit']}}
limits = {}
for name, rel in [('quota','cpu/cpu.cfs_quota_us'),('period','cpu/cpu.cfs_period_us'),
                  ('cpuset','cpuset/cpuset.cpus'),('memory','memory/memory.limit_in_bytes')]:
    p = Path('/sys/fs/cgroup') / rel
    limits[name] = p.read_text().strip() if p.is_file() else None
result['limits'] = limits
vfs = os.statvfs(root)
result['filesystem_available_bytes_not_user_quota'] = vfs.f_bavail * vfs.f_frsize
mp = root / '.local/hpc-sync/latest_manifest.json'
if mp.is_file():
    m = json.loads(mp.read_text())
    result['sync'] = {k: m.get(k) for k in ['sync_id','head','branch','origin']}
    result['sync']['file_count'] = len(m.get('files', []))
result['running'] = []
for p in (root/'research/sync/runs').glob('*/status.json'):
    s = json.loads(p.read_text())
    if s.get('status') == 'running':
        result['running'].append({k: s.get(k) for k in ['run_id','status','pid','started_at']})
whitelist = ['OLLAMA_CONTEXT_LENGTH','OLLAMA_HOST','OLLAMA_MODELS','OLLAMA_NUM_PARALLEL',
             'OLLAMA_MAX_LOADED_MODELS','OLLAMA_NEW_ENGINE','OLLAMA_EXPERIMENT','OLLAMA_NO_CLOUD']
result['ollama_processes'] = []
for p in Path('/proc').iterdir():
    if not p.name.isdigit(): continue
    try:
        args = (p/'cmdline').read_bytes().split(b'\0')
        if not args or 'ollama' not in os.fsdecode(args[0]): continue
        env = dict(x.split(b'=',1) for x in (p/'environ').read_bytes().split(b'\0') if b'=' in x)
        result['ollama_processes'].append({'pid': int(p.name),
            'exe': os.readlink(p/'exe'),
            'safe_argv': [os.fsdecode(x) for x in args[:12] if x],
            'env': {k: os.fsdecode(env[k.encode()]) for k in whitelist if k.encode() in env}})
    except (OSError, ValueError): pass
result['http_get'] = {}
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for endpoint in ['/api/version','/api/ps']:
    try:
        with opener.open('http://127.0.0.1:11434'+endpoint, timeout=5) as response:
            result['http_get'][endpoint] = json.load(response)
    except Exception as exc:
        result['http_get'][endpoint] = {'error': type(exc).__name__, 'detail': str(exc)[:300]}
print(json.dumps(result, ensure_ascii=False, indent=2))
