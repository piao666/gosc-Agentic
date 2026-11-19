"""Restore the two paths touched by the failed closeout sync."""
import hashlib
import json
import os
from pathlib import Path
import shutil

root = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
sync = '20261118T081953Z'
prior = json.loads((root/'.local/hpc-sync/latest_manifest.json').read_bytes())
assert prior['sync_id']=='20261118T074013Z'
archive = Path('/tmp/gosc-sync-'+sync+'.tar.gz')
assert archive.is_file() and not archive.is_symlink()
tmp = Path('/tmp/gosc-runner-closeout-sync-'+sync)
tmp.mkdir(mode=0o700)
readme = root/'research/README.md'
assert hashlib.sha256(readme.read_bytes()).hexdigest()=='3dac488aeeea4064c16768a8e94befa7b88f69cb948d20823317c0aa32c4e0d7'
backup = root/'.local/sync-backups'/sync/'research/README.md'
old = backup.read_bytes()
old_sha = next(e['remote_sha256'] for e in prior['files'] if e['path']=='research/README.md')
assert hashlib.sha256(old).hexdigest()==old_sha
assert len(old)<readme.stat().st_size
shutil.copy2(readme,tmp/'README.md.after_failed_sync')
with readme.open('r+b') as dest:
    dest.write(old)
    dest.truncate()
    dest.flush()
    os.fsync(dest.fileno())
assert readme.read_bytes()==old
partial = root/'research/logs/masbench-t1-driver-2026-11-17/archive_runner_recheck_receipt.py'
assert partial.is_file() and not partial.is_symlink() and partial.stat().st_size==0
shutil.move(str(partial),str(tmp/'archive_runner_recheck_receipt.py.empty'))
assert not partial.exists()
print(json.dumps({'previous_verified_sync':prior['sync_id'],'restored_readme_sha256':old_sha,
                  'partial_evidence_directory':str(tmp),'failed_archive_retained':str(archive)}))
