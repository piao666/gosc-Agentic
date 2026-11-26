"""Independent bounded management readback of the relocated archive."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

ROOT=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
ARCHIVE=Path('/hdd/u202520081000097/gosc-admin-archives/20261126-deployment-admission')
assert os.getuid()==8301880 and Path.cwd()==ROOT
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
begin=time.monotonic()

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

plan=json.loads((ARCHIVE/'migration_plan.json').read_bytes())
receipt=json.loads((ARCHIVE/'migration_receipt.json').read_bytes())
assert receipt['plan_sha256']==sha(ARCHIVE/'migration_plan.json')
checked=[]
for row in plan['entries']:
    source=Path(row['source']); target=Path(row['target'])
    assert ROOT/'.local' in source.parents and ARCHIVE in target.parents
    assert not any(p.is_symlink() for p in (target,*target.parents))
    assert target.is_file() and target.stat().st_uid==os.getuid()
    checked.append({'target':str(target),'size_matches':target.stat().st_size==row['bytes'],
                    'sha_matches':sha(target)==row['sha256'],'source_copy_removed':not source.exists()})
assert all(all(r[k] for k in ('size_matches','sha_matches','source_copy_removed')) for r in checked)
assert all(sha(ROOT/p)==h for p,h in plan['protected_SHA_before'].items())
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip()== \
    '458a96f59b620a02e6872d038b87912eb39e92e4'
quota=json.loads(subprocess.check_output([str(ROOT/'.venv/bin/python'),str(ROOT/
    'research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py')],timeout=10))
result={'kind':'independent administrative SHA readback, not test','passed':True,
        'files_checked':len(checked),'bytes_checked':sum(r['bytes'] for r in plan['entries']),
        'protected_files_unchanged':len(plan['protected_SHA_before']),
        'quota_now':quota,'manifest_sha256':sha(ARCHIVE/'migration_plan.json'),
        'elapsed_seconds':time.monotonic()-begin,'model_calls':0,'service_changes':0,
        'all_original_bytes_retained_on_HDD':True,'old_run_manifests_modified':False}
with (ARCHIVE/'independent_readback.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps(result))
