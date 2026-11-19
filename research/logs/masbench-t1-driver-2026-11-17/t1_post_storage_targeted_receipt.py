"""Record scoped transfer bundles without overwriting older evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLES = ROOT/'.local/t1a-snapshot-archive-20261118'
RUNS = {'hpc-masbench-t1-post-storage-contract-20261119',
        'hpc-masbench-t1b-post-storage-20261119','hpc-masbench-t1b-post-storage-failure-audit-20261119'}
BUNDLE_NAMES = ('t1-post-storage-run-only-transfer.tar.gz','t1-post-storage-failure-audit-transfer.tar.gz')
SCOPE = 't1-post-storage'
if sys.argv[1:]==['--cold-load']:
    RUNS = {'hpc-masbench-t1-cold-load-fixture-20261119','hpc-masbench-t1-cold-load-20261119',
            'hpc-masbench-t1-cold-load-audit-20261119','hpc-masbench-t1-cold-load-fixture-v2-20261119',
            'hpc-masbench-t1-cold-load-v2-20261119','hpc-masbench-t1-cold-load-audit-v2-20261119'}
    BUNDLE_NAMES = ('t1-cold-load-transfer.tar.gz',)
    SCOPE = 't1-cold-load'
elif sys.argv[1:]==['--formal']:
    RUNS = {'hpc-masbench-t1b-formal-contract-20261119','hpc-masbench-t1b-formal-20261119',
            'hpc-masbench-t1b-formal-audit-20261119','hpc-masbench-t1b-formal-audit-detail-20261119'}
    BUNDLE_NAMES = ('t1-formal-transfer.tar.gz','t1-formal-audit-detail-transfer.tar.gz')
    SCOPE = 't1-formal'
elif sys.argv[1:]==['--formal-runner-retest-fixture']:
    RUNS = {'hpc-masbench-t1b-formal-runner-retest-contract-20261119'}
    BUNDLE_NAMES = ('t1-formal-runner-retest-fixture-transfer.tar.gz',)
    SCOPE = 't1-formal-runner-retest-fixture'
elif sys.argv[1:]==['--formal-runner-retest']:
    RUNS = {'hpc-masbench-t1b-formal-runner-retest-20261119',
            'hpc-masbench-t1b-formal-runner-retest-audit-20261119'}
    BUNDLE_NAMES = ('t1-formal-runner-retest-transfer.tar.gz',)
    SCOPE = 't1-formal-runner-retest'
elif sys.argv[1:]:
    raise SystemExit('unknown receipt scope')
data, bundle_info, encountered = [], [], set()
for name in BUNDLE_NAMES:
    path = BUNDLES/name
    with tarfile.open(path,'r:gz') as archive:
        entries = json.load(archive.extractfile('manifest.json'))
    bundle_info.append({'name':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for entry in entries:
        target = Path(entry['path'])
        assert target.parts[:3]==('research','sync','runs') and target.parts[3] in RUNS and '..' not in target.parts
        encountered.add(target.parts[3])
        local = ROOT/target
        assert local.resolve()==local and not local.is_symlink() and local.stat().st_size==entry['size']
        with local.open('rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==entry['sha256']
        data.append(dict(entry,transfer_status='copied'))
assert encountered==RUNS and len(data)==len({x['path'] for x in data})
ident = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+f'-{SCOPE}-scoped'
record = {'sync_id':ident,'direction':'hpc_to_local','source_host':'hpc',
          'scope':'Only the selected newly registered run directories','run_ids':sorted(RUNS),
          'scope_complete':True,'files':data,'bundles':bundle_info,
          'bytes_verified':sum(row['size'] for row in data)}
body = (json.dumps(record,indent=2)+'\n').encode()
destination = ROOT/'research/sync/receipts'/(ident+'.json')
with destination.open('xb') as local:
    local.write(body)
remote = '/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/receipts/'+destination.name
source = f'''from pathlib import Path
import hashlib, os
p = Path({remote!r})
assert os.getuid()==8301880
with p.open('xb') as out:
    out.write({body!r})
    out.flush()
    os.fsync(out.fileno())
assert hashlib.sha256(p.read_bytes()).hexdigest()=={hashlib.sha256(body).hexdigest()!r}
'''
subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','hpc',
    '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -'],
    input=source.encode(),check=True,timeout=25)
print(json.dumps({'receipt':str(destination),'file_count':len(data),'verified_bytes':record['bytes_verified']}))
