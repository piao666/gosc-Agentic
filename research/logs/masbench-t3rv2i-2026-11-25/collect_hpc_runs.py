"""Scoped verified run transfer; never inventories/pulls old private outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
REMOTE = '/home/u202520081000097/jupyterlab/Paper/gosc'
CAP = 64 * 1024**2


def digest(body):
    return hashlib.sha256(body).hexdigest()


def remote(source):
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hpc', 'python3', '-'],
                       input=source.encode(), capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runs', nargs='+')
    args = parser.parse_args()
    assert ROOT == Path('E:/gosc')
    assert all(re.fullmatch(r'hpc-t3rv2i-[a-z0-9-]+', r) for r in args.runs)
    tag = '20261126-t3rv2i-' + uuid.uuid4().hex[:10]
    source = '''
from pathlib import Path
import hashlib,json,os,tarfile
root=Path(ROOT)
assert os.getuid()==8301880 and root.resolve()==root
files=[]
states={}
for rid in IDS:
    base=root/'research/sync/runs'/rid
    state=json.loads((base/'status.json').read_bytes())
    assert state['status']!='running'
    states[rid]=state
    for p in sorted(base.rglob('*')):
        rel=p.relative_to(base)
        if rel.parts[0]=='pytest-tmp':continue
        assert not p.is_symlink()
        if p.is_file():
            b=p.read_bytes()
            files.append(dict(path=p.relative_to(root).as_posix(),size=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert sum(f['size'] for f in files)<=67108864
archive=Path('/tmp/'+TAG+'.tar.gz')
assert not archive.exists()
with tarfile.open(str(archive),'w:gz',compresslevel=1,dereference=True) as tar:
    for f in files:tar.add(str(root/f['path']),arcname=f['path'],recursive=False)
print(json.dumps(dict(files=files,states=states,archive=str(archive),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
'''
    value = json.loads(remote('ROOT='+repr(REMOTE)+'\nIDS='+repr(args.runs)+'\nTAG='+repr(tag)+'\n'+source))
    local_archive = ROOT/'.local/hpc-runs'/(tag+'.tar.gz')
    local_archive.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['scp','-q','-o','BatchMode=yes','hpc:'+value['archive'],str(local_archive)],check=True)
    assert digest(local_archive.read_bytes()) == value['archive_sha256']
    expected = {f['path']: f for f in value['files']}
    with tarfile.open(local_archive) as tar:
        assert set(tar.getnames()) == set(expected)
        for member in tar.getmembers():
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            dest = ROOT/member.name
            assert ROOT in dest.resolve().parents
            body = tar.extractfile(member).read()
            assert len(body) == expected[member.name]['size'] and digest(body) == expected[member.name]['sha256']
            if dest.exists() and digest(dest.read_bytes()) != digest(body):
                backup = ROOT/'.local/hpc-runs/pull-backups'/tag/member.name
                backup.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dest,backup)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(body)
            expected[member.name]['local_sha256'] = digest(dest.read_bytes())
    restored = 0
    artifact_checks = {}
    for rid in args.runs:
        base = ROOT/'research/sync/runs'/rid
        archive = base/'outputs/fixture-prefix-raw.tar.gz'
        preservation = base/'outputs/storage_receipt.json'
        if archive.is_file() and preservation.is_file():
            stored = json.loads(preservation.read_bytes())
            assert digest(archive.read_bytes()) == stored['archive_sha256']
            with tarfile.open(archive) as tar:
                assert set(tar.getnames()) == set(stored['files'])
                for member in tar.getmembers():
                    assert member.isfile() and '..' not in Path(member.name).parts and not Path(member.name).is_absolute()
                    data = tar.extractfile(member).read()
                    assert digest(data) == stored['files'][member.name]
                    target = base/'outputs'/member.name
                    assert (base/'outputs').resolve() in target.resolve().parents
                    if target.exists():
                        assert digest(target.read_bytes()) == digest(data)
                    else:
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(data)
                    restored += 1
        recorded = json.loads((base/'artifacts.json').read_bytes())['files']
        checked = 0
        for item in recorded:
            p = base/item['path']
            assert p.is_file() and p.stat().st_size == item['size'] and digest(p.read_bytes()) == item['sha256']
            checked += 1
        artifact_checks[rid] = checked
    receipt = dict(schema='t3rv2i-scoped-complete-transfer-v1',run_ids=args.runs,states=value['states'],
                   files=list(expected.values()),all_outputs_mirrored=True,
                   archived_original_files_restored_locally=restored,original_artifact_hash_checks=artifact_checks,
                   pytest_transient_trees='excluded per official channel; regular fixture records preserved in fixture-journals.tar.gz',
                   bytes=sum(f['size'] for f in value['files']),archive_sha256=value['archive_sha256'])
    data=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
    target=ROOT/'research/sync/receipts'/(tag+'.json')
    assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    remote('from pathlib import Path\nimport hashlib\np=Path('+repr(REMOTE+'/research/sync/receipts/'+target.name)+')\np.parent.mkdir(parents=True,exist_ok=True)\nassert not p.exists()\np.write_bytes('+repr(data)+')\nassert hashlib.sha256(p.read_bytes()).hexdigest()=='+repr(digest(data))+'\n')
    print(json.dumps(dict(receipt=str(target),files=len(expected),bytes=receipt['bytes'],all_outputs_mirrored=True)))


if __name__ == '__main__':
    main()
