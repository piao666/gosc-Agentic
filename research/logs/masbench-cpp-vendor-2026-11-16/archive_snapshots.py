"""Authorized HPC management archive; no experiment or compiler execution."""
from pathlib import Path
import datetime, errno, gzip, hashlib, json, os, shutil

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
scratch=Path('/tmp/gosc-snapshot-archive-preview-20261116')
run_ids=['hpc-masbench-context-build-20261116']+[
    'hpc-masbench-context-build-v%d-20261116'%i for i in range(2,6)]+[
    'hpc-masbench-cpp-vendor-prepare-20261116','hpc-masbench-cpp-vendor-prepare-v2-20261116']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def copy(src,dst):
    with src.open('rb') as a,dst.open('xb') as b:
        shutil.copyfileobj(a,b,1024*1024);b.flush();os.fsync(b.fileno())
def write(p,obj):
    with p.open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
report={'scope':'user-authorized lossless archive of seven management patches',
        'authorization':'2026-11-16 user: 允许无损压缩并补记失败状态','files':[]}
for run_id in run_ids:
    d=root/'research/sync/runs'/run_id
    raw=d/'source_changes.patch';gz=d/'source_changes.patch.gz'
    temp=scratch/(run_id+'.patch.gz')
    if any(p.is_symlink() for p in [d,raw,gz,temp]):raise RuntimeError('symlink')
    original_sha=sha(raw);original_size=raw.stat().st_size
    restored=hashlib.sha256();n=0
    with gzip.open(temp,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):restored.update(b);n+=len(b)
    if restored.hexdigest()!=original_sha or n!=original_size:raise RuntimeError('restore mismatch')
    bootstrap=False
    try:copy(temp,gz)
    except OSError as e:
        if e.errno not in {errno.EDQUOT,errno.ENOSPC}:raise
        # This path is a newly created partial copy belonging to this operation.
        if gz.exists():gz.unlink()
        backup=scratch/(run_id+'.raw-backup')
        copy(raw,backup)
        if sha(backup)!=original_sha:raise RuntimeError('bootstrap backup mismatch')
        raw.unlink();bootstrap=True
        try:copy(temp,gz)
        except BaseException:
            if gz.exists():gz.unlink()
            copy(backup,raw)
            raise
    if sha(gz)!=sha(temp):raise RuntimeError('archive copy mismatch')
    if not bootstrap:raw.unlink()
    entry={'run_id':run_id,'old_path':str(raw),'old_size':original_size,'old_sha256':original_sha,
           'archive_path':str(gz),'archive_size':gz.stat().st_size,'archive_sha256':sha(gz),
           'restore_verified':True,'local_original_retained':True,'quota_bootstrap':bootstrap,
           'restore_command':'gzip -dc source_changes.patch.gz > source_changes.patch'}
    write(d/'source_changes_archive.json',entry);report['files'].append(entry)
    write(scratch/(run_id+'.archive_receipt.json'),entry)

run=root/'research/sync/runs/hpc-masbench-cpp-vendor-prepare-v2-20261116'
if Path('/proc/50168').exists():raise RuntimeError('child still exists; no state correction')
old=json.loads((run/'status.json').read_text())
copy(run/'status.json',run/'status.before_quota_reconciliation.json')
if (run/'artifacts.json').exists():copy(run/'artifacts.json',run/'artifacts.before_quota_reconciliation.json')
observed=datetime.datetime.now(datetime.timezone.utc).isoformat()
state=dict(old,status='failed',finished_at=None,exit_code=None,
    reconciled_at=observed,reconciliation_reason='Child absent; preparation.json records IncompleteRead; runner finalization failed EDQUOT',
    exact_finish_and_exit='unknown; not reconstructed',elapsed_seconds=None)
(run/'status.json').write_text(json.dumps(state,indent=2)+'\n')
artifacts=[{'path':p.relative_to(run).as_posix(),'size':p.stat().st_size,'sha256':sha(p)}
           for p in sorted((run/'outputs').rglob('*')) if p.is_file()]
(run/'artifacts.json').write_text(json.dumps({'run_id':run.name,'files':artifacts,
    'reconciled_at':observed,'note':'Reconstructed artifact inventory only; original finalization failed'},indent=2)+'\n')
report['status_reconciliation']=state
report['released_bytes']=sum(x['old_size']-x['archive_size'] for x in report['files'])
import sys
sys.path.insert(0,str(root/'scripts'))
from hpc_runs import refresh_dashboard
refresh_dashboard()
write(scratch/'archive_result.json',report)
print(json.dumps(report,ensure_ascii=False))
