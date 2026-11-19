"""Compare the current failed-run immutable journals with its registration index."""
import hashlib
import json
from pathlib import Path

root = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
run = root/'research/sync/runs/hpc-masbench-t1b-runner-recheck-20261118'
items = {row['path']:row for row in json.loads((run/'artifacts.json').read_bytes())['files']}
result = {}
for name in ('outputs/driver/control.jsonl','outputs/driver/campaign/ledger.jsonl'):
    raw = (run/name).read_bytes()
    entries = [json.loads(line) for line in raw.rstrip(b'\0').splitlines()]
    sha = hashlib.sha256(raw).hexdigest()
    result[name] = {'sha256':sha,'registration_sha256':items[name]['sha256'],'matches':sha==items[name]['sha256'],
                    'row_count':len(entries),'tip':entries[-1]['hash'],
                    'additional_control_records':entries[22:] if name.endswith('control.jsonl') else []}
print(json.dumps(result))
