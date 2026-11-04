"""Reuse audited read-only inventory payloads; write a new dated snapshot only."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

LOG = Path(__file__).resolve().parent
PREVIOUS = LOG.parent / 'masbench-reasoning-static-2026-10-30'
PYTHON = '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python'
records = []
for name in ('readonly_environment.py', 'readonly_model_storage.py'):
    source = (PREVIOUS / name).read_bytes()
    tree = ast.parse(source.decode('utf-8'))
    payload = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'REMOTE'
                           for target in node.targets))
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', 'hpc', PYTHON + ' -']
    stem = 'environment' if name == 'readonly_environment.py' else 'model_storage'
    item = dict(source=str((PREVIOUS / name).relative_to(LOG.parents[2])),
                payload_source_sha256=hashlib.sha256(source).hexdigest(), command=command)
    try:
        result = subprocess.run(command, input=payload.encode('utf-8'), capture_output=True, timeout=55)
        (LOG / (stem + '_stdout.json')).write_bytes(result.stdout)
        (LOG / (stem + '_stderr.txt')).write_bytes(result.stderr)
        item['exit_code'] = result.returncode
        if result.returncode == 0:
            item['inventory'] = json.loads(result.stdout)
    except subprocess.TimeoutExpired as error:
        item['status'] = 'ssh_timeout'
        (LOG / (stem + '_stdout.json')).write_bytes(error.stdout or b'')
        (LOG / (stem + '_stderr.txt')).write_bytes(error.stderr or b'')
    records.append(item)
local = {}
for path in ('/api/version', '/api/tags'):
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434' + path, timeout=2) as response:
            local[path] = dict(status='available', response=json.load(response))
    except Exception as error:
        local[path] = dict(status='unavailable', error=type(error).__name__)
record = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='Read-only environment management; no project tests, task or model inference',
              records=records, local_loopback=local, llm_calls=0, models_loaded=False,
              dependencies_installed=False, scientific_runs=[], git_commit_or_push=False)
(LOG / 'inventory.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n',
                                   encoding='utf-8', newline='\n')
print(json.dumps(record, ensure_ascii=False))
