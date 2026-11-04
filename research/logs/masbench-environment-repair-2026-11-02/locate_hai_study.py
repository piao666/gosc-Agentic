"""Read-only bounded lookup for the exact directory explicitly authorized for removal."""
from pathlib import Path
import json
import subprocess

LOG=Path(__file__).resolve().parent
REMOTE=r'''
from pathlib import Path
import json,os,subprocess
home=Path.home();found=[]
for directory,dirs,files in os.walk(home,followlinks=False):
    current=Path(directory);depth=len(current.relative_to(home).parts)
    for name in list(dirs):
        if name.lower()=='hai-study':
            p=current/name
            row={'path':str(p),'resolved':str(p.resolve()),'symlink':p.is_symlink(),'uid':p.stat().st_uid}
            usage=subprocess.run(['du','-x','-s','-B1',str(p)],capture_output=True,text=True,timeout=25)
            row.update(du_exit_code=usage.returncode,allocated=usage.stdout.strip(),stderr=usage.stderr.strip())
            mounts=[]
            for line in Path('/proc/self/mountinfo').read_text().splitlines():
                mount=Path(line.split()[4].replace('\040',' '))
                if mount==p.resolve() or p.resolve() in mount.parents:mounts.append(str(mount))
            row['nested_mounts']=mounts;found.append(row);dirs.remove(name)
    dirs[:]=[name for name in dirs if name not in {'.ssh','.git','.cache','.local','models','.venv','node_modules','__pycache__'} and depth<4]
print(json.dumps({'home':str(home),'uid':os.getuid(),'exact_candidates':found,'deletion_performed':False}))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc',
                  '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -'],
                 input=REMOTE.encode(),capture_output=True,timeout=50)
(LOG/'hai_study_preflight.json').write_bytes(p.stdout)
(LOG/'hai_study_preflight.stderr').write_bytes(p.stderr)
print(p.stdout.decode());print(p.stderr.decode());raise SystemExit(p.returncode)
