"""Copy and verify only this turn's source patches in HPC tmpfs."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/runs')
TMP = Path('/tmp/gosc-t1a-snapshot-archive-20261118')
IDS = [f'hpc-masbench-t1a-{name}-20261118' for name in
       ['contract', 'contract-v2', 'contract-v3', 'evidence-audit']]
TMP.mkdir(mode=0o700)
assert TMP.resolve() == TMP and TMP.stat().st_uid == os.getuid()
rows = []
for run in IDS:
    source = ROOT / run / 'source_changes.patch'
    assert source.is_file() and source.resolve() == source
    target = TMP / (run + '.patch.gz')
    with source.open('rb') as raw, gzip.open(target, 'xb', compresslevel=1) as archive:
        shutil.copyfileobj(raw, archive, 1024 * 1024)
    with source.open('rb') as raw, gzip.open(target, 'rb') as restored:
        original_sha = hashlib.file_digest(raw, 'sha256').hexdigest()
        assert hashlib.file_digest(restored, 'sha256').hexdigest() == original_sha
    with target.open('rb') as archive:
        archive_sha = hashlib.file_digest(archive, 'sha256').hexdigest()
    rows.append({'run_id': run, 'original_size': source.stat().st_size, 'original_sha256': original_sha,
                 'gzip_size': target.stat().st_size, 'gzip_sha256': archive_sha})
print(json.dumps({'files': rows, 'scratch': str(TMP), 'originals_present':True}))
