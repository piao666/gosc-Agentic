"""Local administrative scoped transfer of new runs plus their HDD originals."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import uuid

ROOT=Path(__file__).resolve().parents[3]
REMOTE='/home/u202520081000097/jupyterlab/Paper/gosc'
CAP=32*1024**2


def digest(b):return hashlib.sha256(b).hexdigest()
def remote(code):
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','hpc','python3','-'],input=code.encode(),capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout


def main():
    parser=argparse.ArgumentParser();parser.add_argument('runs',nargs='+');args=parser.parse_args()
    assert ROOT==Path('E:/gosc')
    assert all(r.startswith('hpc-t3rv2i-task-') and all(c.isalnum() or c=='-' for c in r) for r in args.runs)
    tag='20261126-t3rv2t-'+uuid.uuid4().hex[:10]
    code='ROOT='+repr(REMOTE)+'\nIDS='+repr(args.runs)+'\nTAG='+repr(tag)+'\n'+'''
import hashlib,json,os,tarfile
from pathlib import Path
root=Path(ROOT);assert os.getuid()==8301880
files=[];states={};omitted_links=[]
def add(p,target):
    assert p.is_file() and not p.is_symlink()
    b=p.read_bytes();files.append(dict(remote=str(p),path=target,size=len(b),sha256=hashlib.sha256(b).hexdigest()))
for rid in IDS:
    base=root/'research/sync/runs'/rid
    state=json.loads((base/'status.json').read_bytes());assert state['status'] not in ('running','planned');states[rid]=state
    for p in sorted(base.rglob('*')):
        assert not p.is_symlink()
        if p.is_file():add(p,p.relative_to(root).as_posix())
    inventory=base/'outputs/hdd_inventory.json'
    if inventory.is_file():
        inv=json.loads(inventory.read_bytes());hdd=Path(inv['root'])
        assert hdd==Path('/hdd/u202520081000097/gosc-t3rv2t-contracts')/rid
        current=[p for p in hdd.rglob('*') if p.is_file()]
        assert len(current)==len(inv['files'])
        for entry in inv['files']:
            p=hdd/entry['path'];assert p.stat().st_size==entry['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
            add(p,'research/sync/runs/'+rid+'/outputs/hdd_raw/'+entry['path'])
assert len({f['path'] for f in files})==len(files)
assert sum(f['size'] for f in files)<=33554432
archive=Path('/tmp/'+TAG+'.tar.gz');assert not archive.exists()
with tarfile.open(str(archive),'w:gz',compresslevel=1,dereference=True) as tar:
    for row in files:tar.add(row['remote'],arcname=row['path'],recursive=False)
print(json.dumps(dict(files=files,states=states,archive=str(archive),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),omitted_transient_symlinks=omitted_links)))
'''
    value=json.loads(remote(code))
    archive=ROOT/'.local/hpc-runs'/(tag+'.tar.gz');archive.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['scp','-q','-o','BatchMode=yes','hpc:'+value['archive'],str(archive)],check=True)
    assert digest(archive.read_bytes())==value['archive_sha256']
    expected={r['path']:r for r in value['files']}
    with tarfile.open(archive) as tar:
        assert set(tar.getnames())==set(expected)
        for member in tar.getmembers():
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            target=ROOT/member.name;assert ROOT in target.resolve().parents
            body=tar.extractfile(member).read();row=expected[member.name]
            assert len(body)==row['size'] and digest(body)==row['sha256']
            if target.exists():assert digest(target.read_bytes())==row['sha256']
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
            row['local_sha256']=digest(target.read_bytes())
    receipt=dict(schema='t3rv2t-scoped-complete-transfer-v1',run_ids=args.runs,states=value['states'],
        files=list(expected.values()),bytes=sum(r['size'] for r in value['files']),
        all_outputs_mirrored=True,HDD_originals_retained=True,
        omitted_transient_symlinks=value['omitted_transient_symlinks'],archive_sha256=value['archive_sha256'])
    raw=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
    target=ROOT/'research/sync/receipts'/(tag+'.json');target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes(raw)
    remote('from pathlib import Path\nimport hashlib\np=Path('+repr(REMOTE+'/research/sync/receipts/'+target.name)+')\np.parent.mkdir(parents=True,exist_ok=True)\nassert not p.exists()\np.write_bytes('+repr(raw)+')\nassert hashlib.sha256(p.read_bytes()).hexdigest()=='+repr(digest(raw))+'\n')
    print(json.dumps(dict(receipt=str(target),files=len(expected),bytes=receipt['bytes'],all_outputs_mirrored=True)))


if __name__=='__main__':main()

