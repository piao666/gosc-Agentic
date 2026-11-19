"""Persist gzip for this turn's remaining patches, retaining local raw copies."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

root = Path('/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs')
tmp = Path('/tmp/gosc-t1a-snapshot-archive-20261118')
assert tmp.resolve() == tmp and tmp.stat().st_uid == os.getuid()
rows = []
for name in ['evidence-audit-v2', 'contract-v4', 'evidence-audit-v3']:
    run = 'hpc-masbench-t1a-' + name + '-20261118'
    source = root / run / 'source_changes.patch'
    assert source.resolve() == source
    archive = tmp / (run + '.patch.gz')
    original = tmp / (run + '.patch')
    target = source.with_suffix('.patch.gz')
    assert not target.exists() and not original.exists()
    with source.open('rb') as raw, gzip.open(archive, 'xb', compresslevel=1) as dst:
        shutil.copyfileobj(raw, dst, 1024 * 1024)
    with source.open('rb') as raw, gzip.open(archive, 'rb') as restored:
        original_sha = hashlib.file_digest(raw, 'sha256').hexdigest()
        assert hashlib.file_digest(restored, 'sha256').hexdigest() == original_sha
    size = source.stat().st_size
    shutil.move(str(source), str(original))
    with original.open('rb') as raw:
        assert hashlib.file_digest(raw, 'sha256').hexdigest() == original_sha
    with archive.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst, 1024 * 1024)
        dst.flush()
        os.fsync(dst.fileno())
    with gzip.open(target, 'rb') as restored:
        assert hashlib.file_digest(restored, 'sha256').hexdigest() == original_sha
    with target.open('rb') as dst:
        archive_sha = hashlib.file_digest(dst, 'sha256').hexdigest()
    row = {'run_id':run, 'original_sha256':original_sha, 'original_size':size,
           'archive_sha256':archive_sha, 'archive_size':target.stat().st_size,
           'original_retained_tmpfs':str(original), 'local_raw_mirrored_before_archive':True,
           'restore':'gzip -dc source_changes.patch.gz > source_changes.patch'}
    with (root / run / 'source_changes_archive.json').open('x') as output:
        json.dump(row, output, indent=2)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    rows.append(row)
print(json.dumps({'archives':rows,
    'released_bytes_before_sidecars':sum(x['original_size']-x['archive_size'] for x in rows)}))
