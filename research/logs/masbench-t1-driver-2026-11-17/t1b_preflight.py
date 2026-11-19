"""Read-only service identity and occupancy snapshot before T1-B approval file."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
state = json.loads((root/'.local/ollama/service.json').read_bytes())
pid = state['pid']
proc = Path('/proc')/str(pid)
exe = (proc/'exe').resolve()
keys = ['OLLAMA_HOST','OLLAMA_CONTEXT_LENGTH','OLLAMA_NUM_PARALLEL',
        'OLLAMA_MODELS','OLLAMA_MAX_LOADED_MODELS']
env = dict(x.split('=',1) for x in (proc/'environ').read_bytes().decode().split('\0') if '=' in x)
def run(*args):
    return subprocess.check_output(args, text=True, timeout=5).strip()
def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()
rows = []
for f in (root/'research/sync/runs').glob('*/status.json'):
    if json.loads(f.read_bytes()).get('status') == 'running':
        rows.append(f.parent.name)
listeners = run('ss','-Hlnpt','sport = :11434')
connections = run('ss','-Hnt','state','established','sport = :11434 or dport = :11434')
print(json.dumps({
    'host':run('hostname'), 'uid':os.getuid(), 'head':run('git','-C',str(root),'rev-parse','HEAD'),
    'service_pid':pid, 'service_uid':proc.stat().st_uid,
    'service_stamp':(proc/'stat').read_text().rsplit(') ',1)[1].split()[19],
    'service_binary':str(exe), 'service_binary_sha256':sha(exe), 'service_env':{k:env.get(k) for k in keys},
    'loopback_listener_count':len(listeners.splitlines()), 'loopback_own_listener':f'pid={pid},' in listeners,
    'established_connections':len(connections.splitlines()), 'registered_running':rows,
    'helper_sha256':sha('/tmp/gosc-hpc-masbench-context-build-v3-20261116/context-counter'),
    'gpu':run('nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader'),
    'lease_marker':(root/'.local/t1-service.lock').stat().st_size
        if (root/'.local/t1-service.lock').exists() else None,
    'http_requests':0, 'model_calls':0,
}))
