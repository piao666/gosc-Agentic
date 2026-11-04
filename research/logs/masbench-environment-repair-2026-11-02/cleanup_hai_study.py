"""HPC-only exact-target deletion explicitly authorized by the user; never follows symlink targets."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
target=Path('/home/u202520081000097/jupyterlab/hai-study')
assert os.name=='posix' and os.getuid()==8301880
assert target.is_dir() and not target.is_symlink()
assert target.resolve()==target and target.parent==root.parents[1]
assert target.stat().st_uid==os.getuid()
protected=[root,root.parents[1]/'models',Path.home()/'.ssh']
assert all(p!=target and target not in p.parents and p not in target.parents for p in protected)
for line in Path('/proc/self/mountinfo').read_text().splitlines():
    mount=Path(line.split()[4].replace('\\040',' '))
    assert mount!=target and target not in mount.parents,'Nested mount; preserved'
active=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        if proc.stat().st_uid!=os.getuid():continue
        for field in ['cwd','exe']:
            path=(proc/field).resolve()
            if path==target or target in path.parents:active.append({'pid':proc.name,'field':field,'path':str(path)})
    except (OSError,RuntimeError):pass
assert not active,active
out=Path(os.environ['GOSC_OUTPUT_DIR'])
usage=subprocess.run(['du','-x','-s','-B1',str(target)],capture_output=True,text=True,check=True,timeout=30)
before={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target':str(target),
        'allocated_before':int(usage.stdout.split()[0]),'uid':os.getuid(),
        'authorization':'User explicitly said hai-study directory may be cleared',
        'protected_paths':[str(p) for p in protected],'active_processes':active}
(out/'cleanup_before.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.rmtree(target)
assert not target.exists()
after={**before,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'target_exists_after':False,'actual_quota_reclaimed_bytes':None,
       'note':'Allocated pre-delete size is not guaranteed reclaimed quota when hardlinks/shared extents exist',
       'protected_paths_exist_after':{str(p):p.exists() for p in protected}}
(out/'cleanup_after.json').write_text(json.dumps(after,indent=2)+'\n')
print(json.dumps(after))
