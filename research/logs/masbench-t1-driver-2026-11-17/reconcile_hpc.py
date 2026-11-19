"""Management-only CAS Git reconciliation; no checkout/reset or experiments."""
from pathlib import Path
import hashlib,json,subprocess
root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
def git(*a):return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
old='916289ba20fd9808a3673af0aebf175bfc830ccc';new='d5f5522f99872d7453ef54cce06c9ae941846877'
assert git('rev-parse','HEAD')==old
assert git('remote','get-url','origin')=='https://github.com/piao666/gosc-Agentic.git'
assert not [p for p in (root/'research/sync/runs').glob('*/status.json') if json.loads(p.read_bytes()).get('status')=='running']
frozen=json.loads((root/'research/artifacts/native-masbench-20261104/native_frozen.json').read_bytes())
for name,sha in frozen['source_sha256'].items():
    assert hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==sha,name
idx=root/'.git/index';index_sha=hashlib.sha256(idx.read_bytes()).hexdigest()
subprocess.run(['git','-C',str(root),'fetch','/tmp/gosc-t1-base-d5.bundle','HEAD'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert git('merge-base','--is-ancestor',old,new)==''
subprocess.run(['git','-C',str(root),'update-ref','refs/heads/research/progress-audit-2026-10-19',new,old],check=True)
assert hashlib.sha256(idx.read_bytes()).hexdigest()==index_sha
print(json.dumps({'old_head':old,'new_head':git('rev-parse','HEAD'),'frozen_sources_verified':len(frozen['source_sha256']),
    'real_index_unchanged':True,'index_sha256':index_sha,'working_tree_rewritten':False,'project_compute':False}))
