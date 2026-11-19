"""Classify paths touched by the failed closeout sync without modifying them."""
import hashlib
import json
from pathlib import Path
import tarfile

root = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
verified = json.loads((root/'.local/hpc-sync/latest_manifest.json').read_bytes())
assert verified['sync_id']=='20261118T074013Z'
archive = max(Path('/tmp').glob('gosc-sync-*.tar.gz'),key=lambda p:p.stat().st_mtime)
assert archive.is_file() and not archive.is_symlink()
with tarfile.open(archive,'r:gz') as bundle:
    attempt = json.load(bundle.extractfile('meta/manifest.json'))
assert attempt['head']==verified['head'] and attempt['sync_id']>verified['sync_id']
previous = {row['path']:row['remote_sha256'] for row in verified['files']}
rows = []
for item in attempt['files']:
    path = item['path']
    expected = item['remote_sha256']
    old = previous.get(path)
    if old==expected:
        continue
    current = root/path
    actual = hashlib.sha256(current.read_bytes()).hexdigest() if current.is_file() else None
    entry = {'path':path,'state':'updated' if actual==expected else 'prior' if actual==old else 'partial',
             'expected':expected,'prior':old,'observed':actual}
    if entry['state']=='partial':
        backup = root/'.local/sync-backups'/attempt['sync_id']/path
        entry['backup_sha256'] = hashlib.sha256(backup.read_bytes()).hexdigest() if backup.is_file() else None
    rows.append(entry)
critical = [p for p in previous if p.endswith(('live_driver.py','masbench_t1b_live.py','masbench_t1b_runner_recheck_plan.json',
                                              'masbench_t1b_runner_recheck_authorization.json'))]
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==previous[p] for p in critical)
print(json.dumps({'previous_verified_sync':verified['sync_id'],'failed_sync':attempt['sync_id'],
                  'archive_retained':str(archive),'changes':rows,'critical_live_inputs_unchanged':len(critical)}))
