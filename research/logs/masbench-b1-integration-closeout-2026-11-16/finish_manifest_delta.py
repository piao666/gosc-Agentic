"""Management-only completion of one verified interrupted source manifest.

No simulations/tests, Git mutations, remote result edits or general cleanup.
Delete only the known temporary transport after exact SHA verification; all
remaining files are checked against their original normalized payload hashes.
"""
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
LOG=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import remote_script


def main():
    prior=ROOT/'research/logs/masbench-b1-integration-2026-11-10'
    info=json.loads((prior/'failed_sync_archive_inventory.json').read_bytes())
    m=info['manifest']
    allowed={x['path'] for x in json.loads((prior/'partial_sync_mismatches.json').read_bytes())['mismatches']}
    assert m['sync_id']=='20261110T035141Z' and len(m['files'])==871
    payload={}
    for e in m['files']:
        raw=(ROOT/e['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=e['source_sha256']:
            raise RuntimeError('Local source drift: '+e['path'])
        normalized=raw.replace(b'\r\n',b'\n') if e['normalized_lf'] else raw
        # Some LF sources have normalized_lf=False, already canonical.
        if hashlib.sha256(normalized).hexdigest()!=e['remote_sha256']:
            raise RuntimeError('Normalized source hash mismatch: '+e['path'])
        if e['path'] in allowed:payload[e['path']]=base64.b64encode(normalized).decode()
    source=r'''
import os,json,hashlib,base64,subprocess,shutil
from pathlib import Path
r=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880 and r.resolve()==r
def git(*a):return subprocess.check_output(['git','-C',str(r),*a]).decode().strip()
assert git('rev-parse','HEAD')==m['head']=='4754bede84bb6e6defd8e646a63e81ccd6a20b4b'
assert git('remote','get-url','origin')==m['origin']=='https://github.com/piao666/gosc-Agentic.git'
assert not [p for p in (r/'research/sync/runs').glob('*/status.json') if json.loads(p.read_text()).get('status')=='running']
bad=[]
for e in m['files']:
 p=r/e['path']
 if p.is_symlink():raise RuntimeError('Symlink target: '+e['path'])
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=e['remote_sha256']:bad.append(e['path'])
if set(bad)-set(payload):raise RuntimeError('Unexpected remote source changes: '+repr(set(bad)-set(payload)))
for e in m['files']:
 if e['path'] not in bad:continue
 p=Path(e['path'])
 assert not p.is_absolute() and '..' not in p.parts and '.git' not in p.parts
 assert p.parts[0]=='research' and not str(p).startswith(('research/sync/runs/','research/sync/receipts/'))
 assert hashlib.sha256(base64.b64decode(payload[e['path']])).hexdigest()==e['remote_sha256']
archive=Path('/tmp/gosc-sync-20261110T035141Z.tar.gz')
released=0
if archive.exists():
 assert archive.resolve()==archive and not archive.is_symlink() and archive.stat().st_uid==8301880
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==archive_sha
 released=archive.stat().st_size
 archive.unlink()
backup=r/'.local/sync-backups'/m['sync_id']
for e in m['files']:
 if e['path'] not in bad:continue
 dst=r/e['path']
 assert r in dst.resolve().parents
 if dst.exists():
  assert dst.is_file() and not dst.is_symlink()
  saved=backup/e['path']
  if not saved.exists():
   saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
 dst.parent.mkdir(parents=True,exist_ok=True)
 tmp=dst.with_name(dst.name+'.repair-20261116.tmp')
 assert not tmp.exists()
 with tmp.open('xb') as f:
  f.write(base64.b64decode(payload[e['path']]))
  f.flush();os.fsync(f.fileno())
 os.chmod(tmp,e['mode']);os.replace(tmp,dst)
mismatches=[e['path'] for e in m['files'] if hashlib.sha256((r/e['path']).read_bytes()).hexdigest()!=e['remote_sha256']]
assert not mismatches
target=r/'.local/hpc-sync/latest_manifest.json'
data=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
# Use a real LF; the enclosing script is raw to preserve its source.
data=data[:-2]+b'\n' if data.endswith(b'\\n') else data
data=(json.dumps(m,ensure_ascii=False,indent=2)+chr(10)).encode()
tmp=target.with_name('latest_manifest.repair-20261116.tmp')
assert not tmp.exists()
with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
os.replace(tmp,target)
result={'status':'verified','completed_on':'2026-11-16 Asia/Shanghai','original_sync_id':m['sync_id'],
        'head':git('rev-parse','HEAD'),'file_count':len(m['files']),'repaired_paths':bad,
        'sha256_mismatches':mismatches,'released_only_temp_transport_bytes':released,
        'research_records_deleted':False,'original_backups_preserved':True,
        'new_tests_or_model_calls':0,'source_manifest_sha256':hashlib.sha256(data).hexdigest()}
out=r/'research/logs/masbench-b1-integration-closeout-2026-11-16/repair_receipt.json'
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps(result))
'''
    prefix='m='+repr(m)+'\npayload='+repr(payload)+'\narchive_sha='+repr(info['archive_sha256'])+'\n'
    result=remote_script(prefix+source)
    (LOG/'repair_stdout.txt').write_bytes(result.stdout)
    (LOG/'repair_stderr.txt').write_bytes(result.stderr)
    if result.returncode:raise SystemExit(result.returncode)
    receipt=json.loads(result.stdout)
    (LOG/'repair_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
