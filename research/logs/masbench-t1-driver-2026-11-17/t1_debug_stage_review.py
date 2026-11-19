"""Read back loading progress and preserve the exact bounded server evidence."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
LOG = ROOT/'.local/ollama/service.log'
AUDIT = ROOT/'research/sync/runs/hpc-masbench-t1b-post-storage-failure-audit-20261119/outputs/audit.json'
assert os.getuid()==8301880 and LOG.resolve()==LOG and ARCHIVE.resolve()==ARCHIVE
audit = json.loads(AUDIT.read_bytes())
old = json.loads((ARCHIVE/'t1_499_review_2026-11-19.json').read_bytes())
assert audit['acceptance_passed'] is False and audit['generation_requests']==0
old_end = [row for row in old['entries']['failed_recheck']
           if row['message']=='Load failed' or row['message'].startswith('499 ')]
new = audit['service_log_projection']
new_end = [row for row in new if any((isinstance(event,str) and event in ('load failed','client disconnected during loading'))
                                    or (isinstance(event,dict) and event.get('status')==499) for event in row['events'])]
deny = re.compile(rb'authorization|api[_ -]?key|password|secret|bearer|environment=|config=|env=',re.I)
sha = lambda value: hashlib.sha256(value).hexdigest()
evidence = {}
with LOG.open('rb') as stream:
    for label, rows in [('prior_30s',old_end),('current_60s',new_end)]:
        raw = []
        for row in rows:
            stream.seek(row['offset'])
            line = stream.read(row['bytes'] if 'bytes' in row else row['size'])
            assert sha(line)==row['sha256'] and not deny.search(line)
            raw.append(line)
        data = b''.join(raw)
        with (ARCHIVE/f't1_ollama_{label}_failure_lines_2026-11-19.log').open('xb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        evidence[label]={'bytes':len(data),'sha256':sha(data),'line_sha256':[sha(line) for line in raw]}
    start = next(row['offset'] for row in new if 'runner command started' in row['events'])
    end = next(row['offset'] for row in new if 'client disconnected during loading' in row['events'])
    assert 0<end-start<64*1024
    stream.seek(start)
    block = stream.read(end-start)

patterns = {
    'waiting for runner':'waiting for runner',
    'llama server':'llama server',
    'loading model':'loading model',
    'load_tensors':'load_tensors',
    'loading tensors':'loading tensors',
    'loading tensor':'loading tensor',
    'load model':'load model',
    'model weights':'model weights',
    'offload':'offload',
    'memory':'memory',
    'buffer size':'buffer size',
    'CUDA error':'CUDA error',
    'out of memory':'out of memory',
    'timeout':'timeout',
}
labels = []
for line in block.splitlines():
    text = line.decode(errors='replace')
    hits = [label for keyword,label in patterns.items() if keyword.lower() in text.lower()]
    if hits and not deny.search(line):
        labels.append({'matches':hits,'line_sha256':sha(line)})
receipt = {'host':os.uname().nodename,'utc':datetime.now(timezone.utc).isoformat(),
           'source':str(LOG),'archive':str(ARCHIVE),'archived_failure_lines':evidence,
           'cold_load_interval_bytes':len(block),'cold_load_interval_sha256':sha(block),
           'progress_categories':labels,'additional_http_operations':0}
print(json.dumps(receipt))
