"""Relocate this run's own patch files after verified local gzip copies exist."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs')
TMP = Path('/tmp/gosc-t1a-snapshot-archive-20261118')
assert TMP.resolve() == TMP and TMP.stat().st_uid == os.getuid()
IDS = [f'hpc-masbench-t1a-{name}-20261118' for name in
       ['contract', 'contract-v2', 'contract-v3', 'evidence-audit']]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, obj):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(obj, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


rows = []
for run in IDS:
    directory = ROOT / run
    source = directory / 'source_changes.patch'
    target = directory / 'source_changes.patch.gz'
    archive = TMP / (run + '.patch.gz')
    raw_backup = TMP / (run + '.patch')
    assert source.resolve() == source and archive.resolve() == archive
    assert not target.exists() and not raw_backup.exists()
    original_sha = sha(source)
    with gzip.open(archive, 'rb') as restored:
        assert hashlib.file_digest(restored, 'sha256').hexdigest() == original_sha
    original_size = source.stat().st_size
    shutil.move(str(source), str(raw_backup))
    assert sha(raw_backup) == original_sha
    with archive.open('rb') as old, target.open('xb') as new:
        shutil.copyfileobj(old, new, 1024 * 1024)
        new.flush()
        os.fsync(new.fileno())
    assert sha(target) == sha(archive)
    entry = {'original_size':original_size, 'original_sha256':original_sha,
             'archive_size':target.stat().st_size, 'archive_sha256':sha(target),
             'original_retained_tmpfs':str(raw_backup),
             'local_gzip_copy_verified':True,
             'restore':'gzip -dc source_changes.patch.gz > source_changes.patch'}
    write(directory / 'source_changes_archive.json', entry)
    rows.append(dict(entry, run_id=run))

run = ROOT / IDS[-1]
original = run / 'status.json'
status = json.loads(original.read_bytes())
assert status['status'] == 'running' and status['pid'] is None
for p in Path('/proc').iterdir():
    if p.name.isdigit():
        try:
            args = (p / 'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        assert b'experiments_ext/masbench_t1a_evidence_audit.py' not in args
shutil.copyfile(original, run / 'status.before_quota_reconciliation.json')
output = run / 'outputs/audit.json'
assert json.loads(output.read_bytes())['source_run'] == IDS[2]
reconciled = datetime.now(timezone.utc).isoformat()
status.update(status='failed', reconciliation_reason='runner finalization EDQUOT; audit output retained',
              finished_at=None, exit_code=None, elapsed_seconds=None, reconciled_at=reconciled)
write(run / 'status.quota_reconciled.tmp', status)
(run / 'status.quota_reconciled.tmp').replace(original)
write(run / 'artifacts.json', {'run_id':run.name,
    'files':[{'path':'outputs/audit.json','size':output.stat().st_size,'sha256':sha(output)}],
    'reconciled_at':reconciled})
print(json.dumps({'archives':rows, 'status':status,
    'released_bytes_before_sidecars':sum(x['original_size']-x['archive_size'] for x in rows)}))
