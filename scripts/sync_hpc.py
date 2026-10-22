"""One-way Windows worktree -> HPC sync. No tests, training or remote deletions.

Usage from the local checkout: python scripts/sync_hpc.py
Git-ignored files and credentials are excluded. Text is normalized to LF on HPC.
The receiver preserves remote-only files and backs up changed non-result files.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone

RECEIVER = r'''
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tarfile, tempfile
archive = Path(ARCHIVE)
root = Path(REMOTE_ROOT)
assert str(root) == '/home/u202520081000097/jupyterlab/Paper/gosc'
assert root.parent.resolve() == Path('/home/u202520081000097/jupyterlab/Paper')
with tarfile.open(archive, 'r:gz') as tf:
    manifest = json.load(tf.extractfile('meta/manifest.json'))
    stage = Path(tempfile.mkdtemp(prefix='gosc-bundle-'))
    try:
        bundle = stage / 'repository.bundle'
        bundle.write_bytes(tf.extractfile('meta/repository.bundle').read())
        if not root.exists() or not any(root.iterdir()):
            subprocess.run(['git','clone','--quiet','--no-checkout','--branch',manifest['branch'],str(bundle),str(root)],check=True)
            subprocess.run(['git','-C',str(root),'config','core.autocrlf','false'],check=True)
            subprocess.run(['git','-C',str(root),'checkout','--quiet',manifest['branch']],check=True)
            subprocess.run(['git','-C',str(root),'remote','set-url','origin',manifest['origin']],check=True)
        if not (root / '.git').is_dir():
            raise RuntimeError('Destination is not a managed Git checkout; preserved.')
        head = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],universal_newlines=True).strip()
        origin = subprocess.check_output(['git','-C',str(root),'remote','get-url','origin'],universal_newlines=True).strip()
        if head != manifest['head'] or origin != manifest['origin']:
            raise RuntimeError('Remote Git HEAD/origin differs; reconcile explicitly before sync.')
        for status_file in (root/'research/sync/runs').glob('*/status.json'):
            if json.loads(status_file.read_text(encoding='utf-8')).get('status') == 'running':
                raise RuntimeError('A recorded HPC job is running; pull status first and defer source changes.')
        backup = root / '.local/sync-backups' / manifest['sync_id']
        changed = []
        for entry in manifest['files']:
            rel = Path(entry['path'])
            if rel.is_absolute() or '..' in rel.parts or '.git' in rel.parts:
                raise RuntimeError('Unsafe archive path')
            dst = root / rel
            if root.resolve() not in dst.resolve().parents:
                raise RuntimeError('Destination escapes project directory')
            info = tf.getmember('files/' + entry['path'])
            if not info.isfile():
                raise RuntimeError('Only regular file payloads are supported')
            data = tf.extractfile(info).read()
            if hashlib.sha256(data).hexdigest() != entry['remote_sha256']:
                raise RuntimeError('Payload hash mismatch: ' + str(rel))
            if dst.exists():
                if not dst.is_file() or dst.is_symlink():
                    raise RuntimeError('Preserving non-regular destination: ' + str(rel))
                old = dst.read_bytes()
                if old == data:
                    continue
                if rel.parts[0] == 'results' or str(rel) == 'LICENSE':
                    raise RuntimeError('Protected remote result/license differs: ' + str(rel))
                saved = backup / rel
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dst,saved)
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(data)
            os.chmod(dst, entry['mode'])
            changed.append(entry['path'])
        mismatches = [e['path'] for e in manifest['files'] if hashlib.sha256((root/e['path']).read_bytes()).hexdigest() != e['remote_sha256']]
        if mismatches:
            raise RuntimeError('Post-sync hash mismatch: ' + repr(mismatches))
        evidence = root / '.local/hpc-sync'
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'latest_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':'verified','remote_root':str(root),'head':head,'file_count':len(manifest['files']),'changed_count':len(changed),'sha256_mismatches':mismatches,'sync_id':manifest['sync_id'],'remote_only_files':'preserved','text_line_endings':'LF'},ensure_ascii=False))
    finally:
        shutil.rmtree(stage)
archive.unlink()
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='hpc')
    parser.add_argument('--pull-runs', action='store_true', help='Pull HPC-owned execution records and outputs without uploading source')
    args = parser.parse_args()
    if args.pull_runs:
        raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).with_name('hpc_runs.py')),'pull']))
    root = Path(__file__).resolve().parents[1]
    paths = json.loads((root/'research/workspace_paths.json').read_text(encoding='utf-8'))
    remote_root = paths['hpc_project_root']
    if root != Path(paths['code_root']):
        raise SystemExit('Run this sync helper from the configured local Windows checkout.')
    def git(*cmd):
        return subprocess.check_output(['git','-C',str(root),*cmd])
    def ssh(source):
        result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',args.host,'python3','-'],input=source.encode('utf-8'),capture_output=True)
        if result.stderr:
            print(result.stderr.decode('utf-8',errors='replace'),end='')
        if result.returncode:
            raise RuntimeError(result.stdout.decode('utf-8',errors='replace') + '\nSSH exit ' + str(result.returncode))
        return result.stdout.decode('utf-8',errors='replace')
    names = sorted(set(p.decode('utf-8') for p in git('ls-files','--cached','--others','--exclude-standard','-z').split(b'\0') if p))
    names = [n for n in names if not n.startswith(('research/sync/runs/','research/sync/receipts/')) and n not in {'research/sync/dashboard.json','research/sync/STATUS.md'}]
    # Refuse tracked secrets too; never copy SSH material or environment files.
    forbidden_dirs = {'.ssh','.aws','.venv','__pycache__','.pytest_cache','.local','.git'}
    for name in names:
        p = Path(name)
        if any(x in forbidden_dirs for x in p.parts) or p.name == '.env' or (p.name.startswith('.env.') and p.name != '.env.example') or p.suffix.lower() in {'.pem','.key'}:
            raise RuntimeError('Excluded sensitive/local-only path is tracked: ' + name)
        if not (root/p).is_file() or (root/p).is_symlink():
            raise RuntimeError('Missing or non-regular source; deletion sync is disabled: ' + name)
    modes = {}
    for item in git('ls-files','--stage','-z').split(b'\0'):
        if item:
            meta,name = item.split(b'\t',1)
            modes[name.decode('utf-8')] = 0o755 if meta.startswith(b'100755 ') else 0o644
    sync_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    manifest = {'sync_id':sync_id,'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),'origin':git('remote','get-url','origin').decode().strip(),'working_tree_status':git('-c','core.quotepath=false','status','--short').decode('utf-8'),'source_root':str(root),'remote_root':remote_root,'files':[]}
    text_suffixes = {'.py','.sh','.md','.json','.jsonl','.txt','.ps1','.yml','.yaml','.toml','.ini','.cfg','.csv'}
    local_evidence = root / '.local/hpc-sync'
    local_evidence.mkdir(parents=True,exist_ok=True)
    # Verify connectivity before constructing/uploading the snapshot.
    print(ssh("from pathlib import Path\np=Path("+repr(remote_root)+")\nassert p.parent.is_dir()\nprint('HPC target parent verified')\n").strip())
    with tempfile.TemporaryDirectory(prefix='gosc-sync-') as temp:
        temp = Path(temp)
        bundle = temp/'repository.bundle'
        subprocess.run(['git','-C',str(root),'bundle','create',str(bundle),'--all'],check=True)
        archive = temp/'workspace.tar.gz'
        with tarfile.open(archive,'w:gz',compresslevel=1) as tf:
            for name in names:
                p = root/name
                raw = p.read_bytes()
                data = raw.replace(b'\r\n',b'\n') if p.suffix.lower() in text_suffixes or p.name in {'LICENSE','.gitignore','.gitattributes'} else raw
                entry = {'path':name,'source_sha256':hashlib.sha256(raw).hexdigest(),'remote_sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'mode':modes.get(name,0o644),'normalized_lf':data!=raw}
                manifest['files'].append(entry)
                info = tarfile.TarInfo('files/'+name)
                info.size,info.mode = len(data),entry['mode']
                tf.addfile(info,io.BytesIO(data))
            tf.add(bundle,arcname='meta/repository.bundle')
            data = json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
            info = tarfile.TarInfo('meta/manifest.json')
            info.size = len(data)
            tf.addfile(info,io.BytesIO(data))
        remote_archive = '/tmp/gosc-sync-'+sync_id+'.tar.gz'
        subprocess.run(['scp','-q','-o','BatchMode=yes',str(archive),args.host+':'+remote_archive],check=True)
        output = ssh('ARCHIVE='+repr(remote_archive)+'\nREMOTE_ROOT='+repr(remote_root)+'\n'+RECEIVER)
        print(output,end='')
        receipt = json.loads(output.strip().splitlines()[-1])
        (local_evidence/'latest_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (local_evidence/'latest_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
