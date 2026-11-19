"""Preserve current raw snapshots and compact their verified HPC copies."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs')
STAGE = Path('/tmp/gosc-t1b-quota-recovery-20261118')
SNAPSHOTS = {
    'hpc-masbench-t1b-live-20261118': '24fe95eee9df060b80d0802c8484a0ad21c203e62eb9708b80dfe0eedc7ff5f3',
    'hpc-masbench-t1b-wiring-regression-20261118': '35d2ca2f11f19f51c8e0c0ba11dbda44b0d1fae918a5e04d6603576c8b23b9a9',
}


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


STAGE.mkdir(mode=0o700)
rows = []
for run_id, sha in SNAPSHOTS.items():
    run = ROOT / run_id
    source = run / 'source_changes.patch'
    backup = STAGE / (run_id + '.patch')
    compressed = STAGE / (run_id + '.patch.gz')
    target = run / 'source_changes.patch.gz'
    record = run / 'source_changes_archive.json'
    assert source.resolve() == source and digest(source) == sha
    assert json.loads((run / 'status.json').read_bytes())['status'] in ('failed', 'completed')
    assert not target.exists() and not record.exists()
    shutil.copyfile(source, backup)
    with backup.open('rb') as original, gzip.open(compressed, 'xb', compresslevel=1) as archive:
        shutil.copyfileobj(original, archive)
    with gzip.open(compressed, 'rb') as restored:
        assert hashlib.file_digest(restored, 'sha256').hexdigest() == sha
    size = source.stat().st_size
    assert digest(backup) == digest(source) == sha
    source.unlink()  # Byte-identical raw evidence remains in both staging and Windows.
    with compressed.open('rb') as original, target.open('xb') as archive:
        shutil.copyfileobj(original, archive)
        archive.flush()
        os.fsync(archive.fileno())
    assert digest(target) == digest(compressed)
    row = {
        'run_id': run_id, 'original_sha256': sha, 'original_size': size,
        'archive_sha256': digest(target), 'archive_size': target.stat().st_size,
        'original_retained_tmpfs': str(backup), 'local_original_sha256_verified': True,
        'restore': 'gzip -dc source_changes.patch.gz > source_changes.patch',
    }
    with record.open('x', encoding='utf-8') as handle:
        json.dump(row, handle, indent=2)
        handle.write('\n')
    rows.append(row)
print(json.dumps({'snapshots': rows, 'released_bytes':sum(r['original_size'] - r['archive_size'] for r in rows)}))
