"""Local-only SSH/file/Git management, no local scientific computation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.hpc_runs import remote_script

LOG = Path(__file__).resolve().parent
OLD = '47389eba9c6e2838139df3aa47863ab88634e97a'
NEW = '253a14b19c4410a4606a40c98b8ba24791c7ee43'
BRANCH = 'research/progress-audit-2026-10-19'
REMOTE_BUNDLE = '/tmp/gosc-information-acceptance-20261027.bundle'

PREFLIGHT = r'''
import hashlib,json,os,pathlib,socket,subprocess,sys
root=pathlib.Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880 and root.is_dir()
def git(*args):return subprocess.check_output(['git','-C',str(root)]+list(args),universal_newlines=True).strip()
manifest=json.loads((root/'.local/hpc-sync/latest_manifest.json').read_text())
bad=[]
for entry in manifest['files']:
 p=root/entry['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['remote_sha256']:bad.append(entry['path'])
running=[]
for p in sorted((root/'research/sync/runs').glob('*/status.json')):
 d=json.loads(p.read_text())
 if d['status']=='running':running.append(dict(run=p.parent.name,pid=d.get('pid')))
limits={}
for key,path in [('quota','/sys/fs/cgroup/cpu/cpu.cfs_quota_us'),('period','/sys/fs/cgroup/cpu/cpu.cfs_period_us'),('cpuset','/sys/fs/cgroup/cpuset/cpuset.cpus'),('memory','/sys/fs/cgroup/memory/memory.limit_in_bytes')]:
 p=pathlib.Path(path);limits[key]=p.read_text().strip() if p.exists() else None
env=subprocess.check_output([str(root/'.venv/bin/python'),'-c','import sys,numpy,pytest;print(sys.executable);print(sys.version);print("numpy="+numpy.__version__+" pytest="+pytest.__version__)'],universal_newlines=True)
print(json.dumps(dict(host=socket.gethostname(),uid=os.getuid(),root=str(root),head=git('rev-parse','HEAD'),branch=git('symbolic-ref','--short','HEAD'),origin=git('remote','get-url','origin'),limits=limits,python=env,running=running,previous_sync=manifest['sync_id'],previous_sync_head=manifest['head'],verified_previous_files=len(manifest['files']),mismatches=bad,git_status=git('status','--short')),ensure_ascii=False))
'''

RECONCILE = r'''
import hashlib,json,os,pathlib,shutil,subprocess
root=pathlib.Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880
old=OLD;new=NEW;branch=BRANCH
def git(*args):return subprocess.check_output(['git','-C',str(root)]+list(args),universal_newlines=True).strip()
assert git('rev-parse','HEAD')==old and git('symbolic-ref','--short','HEAD')==branch
assert git('remote','get-url','origin')=='https://github.com/piao666/gosc-Agentic.git'
for p in (root/'research/sync/runs').glob('*/status.json'):
 assert json.loads(p.read_text())['status']!='running',str(p)
m=json.loads((root/'.local/hpc-sync/latest_manifest.json').read_text())
bad=[e['path'] for e in m['files'] if not (root/e['path']).is_file() or hashlib.sha256((root/e['path']).read_bytes()).hexdigest()!=e['remote_sha256']]
assert not bad,repr(bad)
backup=root/'.local/git-checkpoints/20261027-before-information-acceptance'
backup.mkdir(parents=True,exist_ok=False)
index=pathlib.Path(git('rev-parse','--git-path','index'))
if not index.is_absolute():index=root/index
shutil.copy2(str(index),str(backup/'index'))
(backup/'working.patch').write_bytes(subprocess.check_output(['git','-C',str(root),'diff','--binary','HEAD']))
(backup/'status.txt').write_text(git('status','--short')+'\n')
ref='refs/gosc-transfer/information-20261027'
subprocess.check_call(['git','-C',str(root),'fetch',BUNDLE,'refs/heads/'+branch+':'+ref])
assert git('rev-parse',ref)==new
subprocess.check_call(['git','-C',str(root),'merge-base','--is-ancestor',old,new])
subprocess.check_call(['git','-C',str(root),'update-ref','refs/heads/'+branch,new,old])
subprocess.check_call(['git','-C',str(root),'read-tree',new])
proof=dict(old=old,new=new,previous_sync=m['sync_id'],verified_previous_files=len(m['files']),mismatches=bad,working_files_modified=False,backup=str(backup),action='Strict-descendant ref and index update only; no working-file checkout/reset; next SHA sync supplies source')
(backup/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['preflight', 'reconcile'])
    a = ap.parse_args()
    if a.mode == 'reconcile':
        before = json.loads((LOG / 'preflight.json').read_text(encoding='utf-8'))
        if before['head'] != OLD or before['mismatches'] or before['running']:
            raise RuntimeError('Preflight blocks reconciliation')
        bundle = ROOT / '.local/hpc-sync/information-20261027.bundle'
        bundle.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-C', str(ROOT), 'bundle', 'create', str(bundle), BRANCH, '^'+OLD], check=True)
        subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', str(bundle), 'hpc:'+REMOTE_BUNDLE], check=True)
        source = 'OLD='+repr(OLD)+'\nNEW='+repr(NEW)+'\nBRANCH='+repr(BRANCH)+'\nBUNDLE='+repr(REMOTE_BUNDLE)+'\n'+RECONCILE
    else:
        source = PREFLIGHT
    r = remote_script(source)
    attempt = 1
    while (LOG / (a.mode + '-attempt'+str(attempt)+'-stdout.txt')).exists():
        attempt += 1
    (LOG / (a.mode + '-attempt'+str(attempt)+'-stdout.txt')).write_bytes(r.stdout)
    (LOG / (a.mode + '-attempt'+str(attempt)+'-stderr.txt')).write_bytes(r.stderr)
    if r.returncode:
        raise SystemExit(r.returncode)
    result = json.loads(r.stdout.decode('utf-8').strip().splitlines()[-1])
    (LOG / (a.mode + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if a.mode == 'preflight':
        result.pop('git_status', None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
