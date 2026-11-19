"""Read back the published HDD archive and stage four complete recovery copies."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
import time

ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880 and ARCHIVE.resolve()==ARCHIVE


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


started = time.monotonic()
manifest = json.loads((ARCHIVE/'archive_manifest.json').read_bytes())
assert manifest['source_root']==str(ROOT) and manifest['archive']==str(ARCHIVE)
checksums = {row['path']:row for row in manifest['files']}
assert len(checksums)==manifest['file_count']
expected_sums = ''.join(f"{checksums[name]['sha256']}  {name}\n" for name in sorted(checksums))
assert (ARCHIVE/'SHA256SUMS').read_text(encoding='utf-8')==expected_sums
for name, row in checksums.items():
    relative = PurePosixPath(name)
    item = ARCHIVE/name
    assert not relative.is_absolute() and '..' not in relative.parts and item.resolve()==item
    observed = item.stat()
    assert stat.S_ISREG(observed.st_mode) and observed.st_size==row['size']
check = subprocess.run(['sha256sum','--strict','--check','SHA256SUMS'],cwd=ARCHIVE,
                       capture_output=True,text=True,timeout=90,check=True)
assert len(check.stdout.splitlines())==manifest['file_count'] and not check.stderr
for run_id in manifest['runs']:
    relative = 'research/sync/runs/'+run_id
    state = json.loads((ARCHIVE/relative/'status.json').read_bytes())
    assert state==manifest['runs'][run_id] and state['status']=='completed'
    artifacts = json.loads((ARCHIVE/relative/'artifacts.json').read_bytes())['files']
    for artifact in artifacts:
        row = checksums[relative+'/'+artifact['path']]
        assert row['sha256']==artifact['sha256'] and row['size']==artifact['size']

readback = []
with tempfile.TemporaryDirectory(dir=ARCHIVE.parent,prefix='.restore-drill-') as scratch:
    restored_root = Path(scratch)
    for row in manifest['proposed_ssd_cleanup']:
        name = row['path']
        assert checksums[name]==row
        ssd = ROOT/name
        original = ssd.stat()
        assert ssd.resolve()==ssd and original.st_dev==row['ssd_device'] and original.st_ino==row['ssd_inode']
        assert original.st_size==row['size'] and original.st_nlink==1 and original.st_mtime_ns==row['ssd_mtime_ns']
        assert sha(ssd)==row['sha256']
        restored = restored_root/name
        restored.parent.mkdir(parents=True,exist_ok=True)
        with (ARCHIVE/name).open('rb') as source, restored.open('xb') as dest:
            shutil.copyfileobj(source,dest,length=1024**2)
            dest.flush()
            os.fsync(dest.fileno())
        digest = sha(restored)
        assert digest==row['sha256'] and restored.stat().st_size==row['size']
        readback.append({'path':name,'size':row['size'],'sha256':digest,'matches_ssd':True})

evidence = {'archive':str(ARCHIVE),'checked_utc':datetime.now(timezone.utc).isoformat(),
            'archive_manifest_sha256':sha(ARCHIVE/'archive_manifest.json'),
            'checksum_file_sha256':sha(ARCHIVE/'SHA256SUMS'),
            'files_verified':len(checksums),'bytes_verified':manifest['logical_bytes'],
            'restore_drill_files':readback,'restore_drill_bytes':sum(x['size'] for x in readback),
            'restore_drill_scope':'separate temporary directory on HDD with exact original relative paths',
            'ssd_originals_retained':True,'elapsed_seconds':round(time.monotonic()-started,3)}
with (ARCHIVE/'readback_verification.json').open('x',encoding='utf-8') as stream:
    json.dump(evidence,stream,indent=2)
    stream.write('\n')
    stream.flush()
    os.fsync(stream.fileno())
print(json.dumps(evidence))
