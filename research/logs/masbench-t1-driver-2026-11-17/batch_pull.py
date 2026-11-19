"""Batch this turn's small artifacts. Standard pull verifies the final receipt."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / '.local/t1a-snapshot-archive-20261118/run-transfer.tar.gz'
ids = ['hpc-masbench-t1a-' + name + '-20261118' for name in
       ('contract', 'contract-v2', 'contract-v3', 'contract-v4',
        'evidence-audit', 'evidence-audit-v2', 'evidence-audit-v3')]
paths = ['research/sync/runs/' + run for run in ids]
remote_root = '/home/u202520081000097/jupyterlab/Paper/gosc'
remote_archive = '/tmp/gosc-t1a-batch-v1-20261118.tar.gz'
selections = {
    '--t1b-regression': ['hpc-masbench-t1b-wiring-regression-20261118'],
    '--t1b-quota-failure': ['hpc-masbench-t1b-live-20261118'],
    '--t1b-v2-quota-failure': ['hpc-masbench-t1b-live-v2-20261118'],
    '--t1b-v2-reconciliation': ['hpc-masbench-t1b-live-v2-20261118'],
    '--t1b-live-v3': ['hpc-masbench-t1b-live-v3-20261118'],
    '--t1b-evidence-audit': ['hpc-masbench-t1b-live-evidence-audit-20261118'],
    '--t1-runner-fixtures': ['hpc-masbench-t1-runner-recovery-contract-20261118',
                             'hpc-masbench-t1-runner-recovery-contract-v2-20261118',
                             'hpc-masbench-t1-runner-recovery-audit-20261118'],
    '--t1-runner-recheck': ['hpc-masbench-t1b-runner-recheck-20261118',
                           'hpc-masbench-t1b-runner-recheck-audit-20261118'],
    '--t1-runner-recheck-run-only': ['hpc-masbench-t1b-runner-recheck-20261118'],
    '--t1-post-storage-run-only': ['hpc-masbench-t1-post-storage-contract-20261119',
                                  'hpc-masbench-t1b-post-storage-20261119'],
    '--t1-post-storage-reviewed': ['hpc-masbench-t1-post-storage-contract-20261119',
                                   'hpc-masbench-t1b-post-storage-20261119',
                                   'hpc-masbench-t1b-post-storage-audit-20261119'],
    '--t1-post-storage-failure-audit': ['hpc-masbench-t1b-post-storage-failure-audit-20261119'],
    '--t1-cold-load': ['hpc-masbench-t1-cold-load-fixture-20261119',
                       'hpc-masbench-t1-cold-load-20261119','hpc-masbench-t1-cold-load-audit-20261119',
                       'hpc-masbench-t1-cold-load-fixture-v2-20261119','hpc-masbench-t1-cold-load-v2-20261119',
                       'hpc-masbench-t1-cold-load-audit-v2-20261119'],
    '--t1-formal-fixture': ['hpc-masbench-t1b-formal-contract-20261119'],
    '--t1-formal': ['hpc-masbench-t1b-formal-contract-20261119',
                    'hpc-masbench-t1b-formal-20261119','hpc-masbench-t1b-formal-audit-20261119'],
    '--t1-formal-audit-detail': ['hpc-masbench-t1b-formal-audit-detail-20261119'],
    '--t1-formal-runner-retest-fixture': ['hpc-masbench-t1b-formal-runner-retest-contract-20261119'],
    '--t1-formal-runner-retest': ['hpc-masbench-t1b-formal-runner-retest-20261119',
                                  'hpc-masbench-t1b-formal-runner-retest-audit-20261119'],
}
if len(sys.argv) != 1:
    selection, = sys.argv[1:]
    label = selection.removeprefix('--')
    paths = ['research/sync/runs/' + run for run in selections[selection]]
    ARCHIVE = ARCHIVE.with_name(label + '-transfer.tar.gz')
    remote_archive = '/tmp/gosc-' + label + '-20261118.tar.gz'
remote_code = r"""
import hashlib,io,json,sys,tarfile
from pathlib import Path
root=Path(sys.argv[1])
paths=json.loads(sys.argv[2])
out=Path(sys.argv[3])
cap=int(sys.argv[4])
rows=[]
total=0
with tarfile.open(out,'x:gz',compresslevel=1) as archive:
    for d in paths:
        for p in sorted((root/d).rglob('*')):
            if p.is_symlink():raise RuntimeError('unexpected link')
            if not p.is_file():continue
            b=p.read_bytes()
            total+=len(b)
            if total>cap:raise RuntimeError('transfer cap')
            name=p.relative_to(root).as_posix()
            rows.append({'path':name,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()})
            info=tarfile.TarInfo(name)
            info.size=len(b)
            archive.addfile(info,io.BytesIO(b))
    body=json.dumps(rows).encode()
    info=tarfile.TarInfo('manifest.json')
    info.size=len(body)
    archive.addfile(info,io.BytesIO(body))
"""
import shlex
limit = {'--t1-cold-load':48,'--t1-formal-fixture':56,'--t1-formal':56,'--t1-formal-audit-detail':56,
         '--t1-formal-runner-retest-fixture':56,'--t1-formal-runner-retest':56}.get(
    sys.argv[1] if len(sys.argv)>1 else '',100)
remote = shlex.join([remote_root+'/.venv/bin/python','-',remote_root,json.dumps(paths),remote_archive,str(limit*1024**2)])
subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','hpc',remote],
               input=remote_code.encode(),check=True,timeout=45)
subprocess.run(['scp','-q','-o','BatchMode=yes',f'hpc:{remote_archive}',str(ARCHIVE)],
               check=True,timeout=45)
copied=0
with tarfile.open(ARCHIVE,'r:gz') as archive:
    rows=json.load(archive.extractfile('manifest.json'))
    for row in rows:
        p=Path(row['path'])
        if p.is_absolute() or '..' in p.parts or not any(p.as_posix().startswith(d+'/') for d in paths):
            raise RuntimeError('unexpected path')
        member=archive.getmember(row['path'])
        if not member.isfile():raise RuntimeError('unexpected member')
        data=archive.extractfile(member).read()
        if len(data)!=row['size'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise RuntimeError('artifact digest mismatch')
        dest=ROOT/p
        if dest.resolve()!=dest or dest.is_symlink():raise RuntimeError('unsafe local path')
        if dest.exists():
            previous = dest.read_bytes()
            if previous == data:
                continue
            preserved = dest.with_name('status.before_quota_reconciliation.json')
            if (sys.argv[1:] != ['--t1b-v2-reconciliation'] or dest.name != 'status.json'
                    or not preserved.is_file() or previous != preserved.read_bytes()):
                raise RuntimeError('existing file differs')
            dest.write_bytes(data)
            copied += 1
            continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_name(dest.name+'.partial-t1a-batch')
        with temp.open('xb') as handle:handle.write(data)
        if dest.exists():
            if dest.read_bytes()!=data:raise RuntimeError('concurrent file differs')
            temp.unlink()
        else:os.replace(temp,dest)
        copied+=1
print(json.dumps({'files_checked':len(rows),'files_seeded':copied,'archive_bytes':ARCHIVE.stat().st_size}))
