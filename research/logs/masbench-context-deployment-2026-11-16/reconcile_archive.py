"""Explicit source-archive fast-forward, preserving remote worktree and index."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import remote_script

OLD='4754bede84bb6e6defd8e646a63e81ccd6a20b4b'
NEW='916289ba20fd9808a3673af0aebf175bfc830ccc'
bundle=ROOT/'.local/masbench-context-20261116.bundle'
bundle.parent.mkdir(exist_ok=True)
if not bundle.exists():
    subprocess.run(['git','bundle','create',str(bundle),'research/progress-audit-2026-10-19','^'+OLD],check=True)
sha=hashlib.sha256(bundle.read_bytes()).hexdigest()
remote='/tmp/gosc-context-20261116-'+sha[:12]+'.bundle'
subprocess.run(['scp','-q',str(bundle),'hpc:'+remote],check=True,timeout=60)
source=r'''
from pathlib import Path
import hashlib,json,os,subprocess
r=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880
def git(*args):return subprocess.check_output(['git','-C',str(r),*args]).decode().strip()
assert git('rev-parse','HEAD')==old
assert git('remote','get-url','origin')=='https://github.com/piao666/gosc-Agentic.git'
assert not [p for p in (r/'research/sync/runs').glob('*/status.json') if json.loads(p.read_text()).get('status')=='running']
m=json.loads((r/'.local/hpc-sync/latest_manifest.json').read_text())
assert m['head']==old and m['sync_id']=='20261116T024042Z'
bad=[]
for e in m['files']:
 p=r/e['path']
 if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=e['remote_sha256']:bad.append(e['path'])
assert not bad,repr(bad)
assert hashlib.sha256(Path(bundle_path).read_bytes()).hexdigest()==expected_sha
subprocess.run(['git','-C',str(r),'bundle','verify',bundle_path],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
subprocess.run(['git','-C',str(r),'fetch','--no-tags',bundle_path,'refs/heads/research/progress-audit-2026-10-19'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
subprocess.run(['git','-C',str(r),'merge-base','--is-ancestor',old,new],check=True)
ref=git('symbolic-ref','HEAD')
subprocess.run(['git','-C',str(r),'update-ref',ref,new,old],check=True)
print(json.dumps({'old_head':old,'new_head':git('rev-parse','HEAD'),'checked_manifest_files':len(m['files']),
 'source_mismatches':bad,'worktree_or_index_rewritten':False,'bundle_sha256':expected_sha,
 'remote_bundle_retained':bundle_path,'commit_or_push':False}))
'''
script='old='+repr(OLD)+'\nnew='+repr(NEW)+'\nbundle_path='+repr(remote)+'\nexpected_sha='+repr(sha)+'\n'+source
p=remote_script(script)
(HERE/'archive_reconcile_stdout.json').write_bytes(p.stdout)
(HERE/'archive_reconcile_stderr.txt').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
raise SystemExit(p.returncode)
