"""Recover space and close the stale v2 registration from its raw failure."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
RUN = ROOT / 'research/sync/runs/hpc-masbench-t1b-live-v2-20261118'
TMP = Path('/tmp/gosc-t1b-quota-recovery-20261118')
assert TMP.resolve() == TMP and TMP.stat().st_uid == os.getuid()
sha = lambda value: hashlib.sha256(value).hexdigest()
status_path = RUN / 'status.json'
status_bytes = status_path.read_bytes()
status = json.loads(status_bytes)
assert status['status'] == 'running' and status['pid'] == 50808
assert not Path('/proc/50808').exists()
assert not (RUN / 'outputs/driver/control.jsonl').exists()
assert (RUN / 'outputs/driver/campaign/ledger.jsonl').stat().st_size == 0
assert (ROOT / '.local/t1-service.lock').stat().st_size == 0
error_sha = sha((RUN / 'stderr.log').read_bytes())
assert error_sha == 'e66bd232bc0d237afa91c42fbe3503045224975ade5818611b851e02ebfd45fa'
source = RUN / 'source_changes.patch'
original = source.read_bytes()
original_sha = sha(original)
assert original_sha == 'b240587922e9aaa4821953bcf74904a9dc0aa7bd73c74b6a399bba004929a841'
backup = TMP / (RUN.name + '.patch')
with backup.open('xb') as copy:
    copy.write(original)
assert sha(backup.read_bytes()) == original_sha
archive = gzip.compress(original, compresslevel=1, mtime=0)
assert gzip.decompress(archive) == original
assert not (RUN / 'source_changes.patch.gz').exists()
source.unlink()  # Byte-identical local and temporary raw copies have been verified.
with (RUN / 'source_changes.patch.gz').open('xb') as target:
    target.write(archive)
    target.flush()
    os.fsync(target.fileno())
assert sha((RUN / 'source_changes.patch.gz').read_bytes()) == sha(archive)
record = {
    'original_size':len(original), 'original_sha256':original_sha,
    'archive_size':len(archive), 'archive_sha256':sha(archive), 'original_retained_tmpfs':str(backup),
    'local_original_sha256_verified':True, 'restore':'gzip -dc source_changes.patch.gz > source_changes.patch',
    'stderr_sha256':error_sha, 'http_requests':0, 'generation_requests':0,
    'reason':'EDQUOT during the first ledger write, then during launcher status finalization',
}
with (RUN / 'source_changes_archive.json').open('x', encoding='utf-8') as target:
    json.dump(record, target, indent=2)
with (RUN / 'status.before_quota_reconciliation.json').open('xb') as target:
    target.write(status_bytes)
status.update(status='failed', reconciliation_reason=record['reason'],
              reconciled_at=datetime.now(timezone.utc).isoformat())
staged_status = RUN / 'status.quota_reconciled.tmp'
with staged_status.open('x', encoding='utf-8') as target:
    json.dump(status, target, indent=2)
    target.write('\n')
staged_status.replace(status_path)
print(json.dumps({'status':status, 'source_archive':record}))
