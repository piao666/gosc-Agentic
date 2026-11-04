"""Delete exactly the two user-specified Laya model directories after boundary checks."""
from pathlib import Path
import datetime
import json
import os
import shutil
import subprocess

assert os.name=='posix' and os.getuid()==8301880
base=Path('/home/u202520081000097/NextWork/models')
targets=[base/'laya-multilingual',base/'laya-typed-decisions']
out=Path(os.environ['GOSC_OUTPUT_DIR'])
protected=[Path('/home/u202520081000097/jupyterlab/Paper/gosc'),
           Path('/home/u202520081000097/jupyterlab/models'),Path.home()/'.ssh']
rows=[]
for target in targets:
    assert target.is_dir() and not target.is_symlink() and target.resolve()==target
    assert target.parent==base and target.stat().st_uid==os.getuid()
    assert all(p!=target and target not in p.parents and p not in target.parents for p in protected)
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        mount=Path(line.split()[4].replace('\\040',' '))
        assert mount!=target and target not in mount.parents,'Nested mount; preserved'
    usage=subprocess.run(['du','-x','-s','-B1',str(target)],capture_output=True,text=True,check=True,timeout=25)
    rows.append({'path':str(target),'allocated_before':int(usage.stdout.split()[0])})
active=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        if proc.stat().st_uid!=os.getuid():continue
        for link in [proc/'cwd',proc/'exe']+list((proc/'fd').iterdir()):
            try:path=link.resolve()
            except (OSError,RuntimeError):continue
            if any(path==target or target in path.parents for target in targets):
                active.append({'pid':proc.name,'path':str(path)})
    except (OSError,RuntimeError):pass
assert not active,active
before={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'targets':rows,
        'authorization':'User supplied both exact Laya paths and explicitly authorized deletion',
        'active_target_processes':active,'nextwork_parent_preserved':str(base.parent)}
(out/'cleanup_before.json').write_text(json.dumps(before,indent=2)+'\n')
for target in targets:shutil.rmtree(target)
assert all(not p.exists() for p in targets)
after={**before,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'target_exists_after':{str(p):p.exists() for p in targets},
       'nextwork_parent_exists':base.parent.is_dir(),'predelete_allocated_bytes':sum(r['allocated_before'] for r in rows),
       'actual_quota_reclaimed_bytes':None,'protected_paths_exist':{str(p):p.exists() for p in protected}}
(out/'cleanup_after.json').write_text(json.dumps(after,indent=2)+'\n')
print(json.dumps(after))
