"""Management-only post-run identity and restored-context observation."""
from pathlib import Path
import json,urllib.request
root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
state=json.loads((root/'.local/ollama/service.json').read_text());pid=state['pid']
env=dict(x.split('=',1) for x in Path('/proc',str(pid),'environ').read_bytes().decode().split('\0') if '=' in x)
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with op.open('http://127.0.0.1:11434/api/ps',timeout=5) as f:ps=json.load(f)
print(json.dumps({'pid':pid,'exe':str(Path('/proc',str(pid),'exe').resolve()),
    'context':env.get('OLLAMA_CONTEXT_LENGTH'),'parallel':env.get('OLLAMA_NUM_PARALLEL'),
    'ps':ps,'old_runner_pid_exists':Path('/proc/37396').exists(),'generated':False}))
