"""Authorized metadata-only fast-forward. No checkout/reset/worktree writes.

Executed only on the fixed HPC root, with a verified public Git bundle.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
TARGET = '458a96f59b620a02e6872d038b87912eb39e92e4'
OLD = 'b05ea731277a9467a8baa0b3ed184f1e1c3f5bf0'
BUNDLE = Path('/tmp/gosc-t3rv2i-delta-20261126.bundle')


def git(*args, **kwargs):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], **kwargs)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def main():
    assert os.getuid() == 8301880 and ROOT.resolve() == ROOT
    assert git('rev-parse', 'HEAD').decode().strip() == OLD
    assert git('remote', 'get-url', 'origin').decode().strip() == 'https://github.com/piao666/gosc-Agentic.git'
    for status in (ROOT/'research/sync/runs').glob('*/status.json'):
        assert json.loads(status.read_bytes()).get('status') != 'running', status
    branch = git('symbolic-ref', 'HEAD').decode().strip()
    assert branch == 'refs/heads/research/progress-audit-2026-10-19'
    store = ROOT/'.local/t3rv2i-git-meta-20261126-delta'
    store.mkdir(exist_ok=False)
    gitdir = ROOT/'.git'
    before = {}
    for name in ['HEAD', 'index', 'FETCH_HEAD', 'ORIG_HEAD', 'packed-refs', branch]:
        p = gitdir/name
        if p.is_file():
            raw = p.read_bytes()
            saved = store/name
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(raw)
            assert saved.read_bytes() == raw
            before[name] = {'bytes':len(raw), 'sha256':digest(raw)}
    status_before = git('status', '--porcelain=v1', '-z')
    (store/'status-before.bin').write_bytes(status_before)
    # The original tracked/untracked worktree list is metadata, not task data.
    names = set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split(b'\0'))
    names.update(git('ls-tree', '-r', '--name-only', 'HEAD', '-z').split(b'\0'))
    protected = {}
    for rawname in names:
        if not rawname:
            continue
        name = rawname.decode()
        if name.startswith(('research/sync/runs/', 'research/sync/receipts/')):
            continue
        p = ROOT/name
        if p.is_file() and not p.is_symlink():
            protected[name] = digest(p.read_bytes())
    (store/'worktree-sha-before.json').write_text(json.dumps(protected, sort_keys=True, indent=2)+'\n')
    assert BUNDLE.is_file()
    assert digest(BUNDLE.read_bytes()) == 'a6e9afa7f1cfdd3ac53c1f8a89c03421ed1671f5fe2faf711ccf953289f2d0cd'
    subprocess.run(['git','-C',str(ROOT),'bundle','verify',str(BUNDLE)], check=True)
    subprocess.run(['git','-C',str(ROOT),'-c','gc.auto=0','fetch','--no-tags',str(BUNDLE),branch], check=True)
    assert git('rev-parse', 'FETCH_HEAD').decode().strip() == TARGET
    subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',OLD,TARGET], check=True)
    env = dict(os.environ, GIT_INDEX_FILE=str(store/'candidate-index'))
    subprocess.run(['git','-C',str(ROOT),'read-tree',TARGET], env=env, check=True)
    # No -u: read-tree changes only the candidate index.
    assert digest((gitdir/'index').read_bytes()) == before['index']['sha256']
    subprocess.run(['git','-C',str(ROOT),'update-ref',branch,TARGET,OLD], check=True)
    os.replace(str(store/'candidate-index'), str(gitdir/'index'))
    mismatches = [name for name, h in protected.items()
                  if not (ROOT/name).is_file() or digest((ROOT/name).read_bytes()) != h]
    assert not mismatches, mismatches
    assert git('rev-parse','HEAD').decode().strip() == TARGET
    (store/'status-after.bin').write_bytes(git('status','--porcelain=v1','-z'))
    result = dict(old_head=OLD, target_head=TARGET, backup=str(store),
                  original_metadata=before, worktree_files_verified=len(protected),
                  worktree_mismatches=mismatches, worktree_written=False,
                  method='verified bundle fetch + metadata-only read-tree/update-ref',
                  model_calls=0, old_run_identity_modified=False)
    (store/'receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
