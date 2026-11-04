"""HPC infrastructure metadata repair and bounded temporary allocation after authorized cleanup."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.name=='posix' and os.getuid()==8301880
out=Path(os.environ['GOSC_OUTPUT_DIR'])
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
directory=root/'research/sync/runs/hpc-masbench-model-restore-retry2-20261102'
status_path=directory/'status.json'
old=json.loads(status_path.read_text())
assert old['status']=='running' and not Path('/proc/'+str(old['pid'])).exists()
(out/'retry2_status_before.json').write_text(json.dumps(old,indent=2)+'\n')
new={**old,'status':'failed','finished_at':None,'exit_code':None,'reconciled_at':now,
     'error':'EDQUOT prevented artifacts/status finalization; child is absent; exact exit/end unavailable'}
status_path.write_text(json.dumps(new,indent=2)+'\n')
artifacts=[]
for p in sorted((directory/'outputs').rglob('*')):
    if p.is_file() and not p.is_symlink():
        artifacts.append({'path':p.relative_to(directory).as_posix(),'size':p.stat().st_size,
                          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(directory/'artifacts.json').write_text(json.dumps({'run_id':directory.name,'files':artifacts,'reconciled_at':now},indent=2)+'\n')
failed=root/'research/sync/runs/hpc-hai-study-cleanup-20261102'
assert failed.exists() and not (failed/'status.json').exists() and not (failed/'manifest.json').exists()
manifest={'schema_version':1,'run_id':failed.name,'kind':'infrastructure','stage':'AUTHORIZED-STORAGE-CLEANUP',
          'purpose':'Failed to write initial manifest due to EDQUOT; deletion was not launched',
          'created_at':None,'reconciled_at':now,'command_source':'cleanup_hai_study.py; original local invocation retained',
          'execution_host':os.uname().nodename,'git_commit':'014b85dfc472c45d8ea5f15e83e0c1ed8e938daf'}
(failed/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(failed/'status.json').write_text(json.dumps({'run_id':failed.name,'status':'failed','started_at':None,
    'finished_at':None,'exit_code':None,'pid':None,'reconciled_at':now,'error':'EDQUOT during initial manifest; command not launched'},indent=2)+'\n')
(failed/'artifacts.json').write_text(json.dumps({'run_id':failed.name,'files':[],'reconciled_at':now},indent=2)+'\n')
for name in ['cleanup_before.json','cleanup_after.json']:
    shutil.copyfile(Path('/tmp/gosc-hai-study-cleanup-20261102')/name,out/name)
probe=root/'.local'/('capacity-reserve-'+str(os.getpid()))
capacity={'requested_bytes':5*1024**3,'at_utc':now,'probe_path':str(probe),'allocation_released':False}
fd=None
try:
    fd=os.open(probe,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.posix_fallocate(fd,0,capacity['requested_bytes'])
    capacity.update(status='allocated_successfully',allocated_bytes=os.fstat(fd).st_blocks*512)
except OSError as error:
    capacity.update(status='allocation_failed',errno=error.errno,error=str(error))
finally:
    if fd is not None:os.close(fd)
    if probe.exists():probe.unlink()
    capacity['allocation_released']=not probe.exists()
(out/'capacity_after_cleanup.json').write_text(json.dumps(capacity,indent=2)+'\n')
print(json.dumps({'reconciliation':'recorded failed; unknown exit/end retained as null',
                  'hai_study_deleted':not (root.parents[1]/'hai-study').exists(),'capacity':capacity}))
