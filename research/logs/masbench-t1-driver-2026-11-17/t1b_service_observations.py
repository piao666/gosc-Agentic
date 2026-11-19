"""Extract bounded service observations without copying the private service log."""
from collections import deque
from pathlib import Path
import json
import re
import subprocess

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
LOG = ROOT / '.local/ollama/service.log'
TIMESTAMP = re.compile(r'2026-11-18[T ](?:06|14):0[67]:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)?')
GIN = re.compile(r'\[GIN\] (2026/11/18 - (?:06|14):0[67]:\d\d) \|\s*(\d+)\s*\|[^\n]*?\b(GET|POST)\s+"(/[^"]+)"$')
ENV = (Path('/proc/37483') / 'environ').read_bytes().split(b'\0')
runner_events, routes = [], []
labels = {
    'starting llama server': 'runner_start', 'llama runner started': 'runner_ready',
    'runner terminated': 'runner_terminated', 'runner process has terminated': 'runner_terminated',
    'expiring model': 'model_expiring', 'runner exited': 'runner_exit',
    'server shutdown': 'shutdown', 'client connection closed': 'client_closed',
    'context canceled': 'context_canceled', 'client canceled': 'client_canceled',
}
with LOG.open(encoding='utf-8', errors='replace') as stream:
    for line in deque(stream, maxlen=2500):
        row = GIN.search(line.rstrip())
        if row and row[4] in ('/api/ps', '/api/chat', '/api/version', '/v1/chat/completions'):
            routes.append({'time':row[1], 'status':int(row[2]), 'method':row[3], 'route':row[4]})
        timestamp = TIMESTAMP.search(line)
        if timestamp:
            for phrase, label in labels.items():
                if phrase in line.lower():
                    pid = re.search(r'\bpid=(\d+)\b', line)
                    runner_events.append({'time':timestamp[0], 'event':label,
                                          'logged_pid':int(pid[1]) if pid else None})
                    break
print(json.dumps({
    'keep_alive_setting_present':any(field.startswith(b'OLLAMA_KEEP_ALIVE=') for field in ENV),
    'keep_alive_zero':b'OLLAMA_KEEP_ALIVE=0' in ENV or b'OLLAMA_KEEP_ALIVE=0s' in ENV,
    'service_routes':routes, 'runner_log_events':runner_events,
    'service_direct_children':subprocess.run(
        ['ps','--ppid','37483','-o','pid=,stat=,comm='], capture_output=True, text=True, check=False).stdout.splitlines(),
    'gpu_memory_mb':subprocess.check_output(
        ['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'], text=True).strip(),
    'lease_bytes':(ROOT/'.local/t1-service.lock').stat().st_size,
    'extra_http_operations':0,
}))
