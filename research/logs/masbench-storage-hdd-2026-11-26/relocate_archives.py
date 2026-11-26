"""Authorized bounded archive relocation. No scientific run or model operation.

Only three fixed ignored management directories may move. Every byte is copied,
fsynced and independently read back before any verified source copy is removed.
The HDD manifest preserves original paths and exact rollback identities.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import time

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
HDD = Path('/hdd/u202520081000097')
DEST = HDD/'gosc-admin-archives/20261126-deployment-admission'
SOURCES = ('.local/diagnostic-wheels', '.local/git-checkpoints', '.local/sync-backups')
WHEEL_SHA = {
    'numpy-2.2.6-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl':
    'ba10f8411898fc418a521833e014a77d3ca01c15b0c6cdcce6a0d2897e6dbbdf',
    'numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl':
    '666dbfb6ec68962c033a450943ded891bed2d54e6755e35e5835d63f4f6931d5',
    'manifest.json': '72d15f398f7cc38f924154af96ab36ddd020b1589d4cfbdb2364b5538821dc74'}
CAP = 4*1024**3
start = time.monotonic()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def no_links(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise RuntimeError('symlink path rejected')
    if path.resolve() != path.absolute():
        raise RuntimeError('noncanonical path rejected')
    return path


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def write_new(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    sync_dir(path.parent)


def protected():
    paths = list((ROOT/'extensions/masbench_reasoning').glob('*.py'))
    paths += [ROOT/'extensions/masbench_reasoning/fair_final_v2_prompt.txt',
              ROOT/'scripts/sync_hpc.py', ROOT/'scripts/hpc_runs.py',
              ROOT/'scripts/hpc_ollama.py', ROOT/'.git/HEAD', ROOT/'.git/index',
              ROOT/'research/artifacts/native-masbench-20261104/masbench_development_registry.json']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def quota():
    raw = subprocess.check_output([str(ROOT/'.venv/bin/python'), str(ROOT/
        'research/logs/masbench-t1-driver-2026-11-17/hpc_lustre_quota.py')], timeout=10)
    return json.loads(raw)


def main():
    assert os.getuid() == 8301880 and Path.cwd() == ROOT
    resource.setrlimit(resource.RLIMIT_AS, (256*1024**2, 256*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('300s management cap')))
    signal.alarm(300)
    assert no_links(HDD).stat().st_uid == os.getuid()
    assert HDD.stat().st_dev != ROOT.stat().st_dev
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip() == \
        '458a96f59b620a02e6872d038b87912eb39e92e4'
    for path in (ROOT/'research/sync/runs').glob('*/status.json'):
        assert json.loads(path.read_bytes())['status'] not in ('running', 'planned'), path
    before = protected(); before_quota = quota()
    assert before_quota['volumes']['hdd']['remaining_to_hard_limit_bytes'] > CAP + 64*1024**2
    no_links(DEST)
    DEST.parent.mkdir(mode=0o700, exist_ok=True)
    assert DEST.parent.stat().st_uid == os.getuid() and DEST.parent.stat().st_dev == HDD.stat().st_dev
    DEST.mkdir(mode=0o700, exist_ok=False)
    entries=[]; total=0
    for relative in SOURCES:
        source=no_links(ROOT/relative)
        assert source.is_dir() and source.stat().st_uid == os.getuid()
        for directory, dirs, names in os.walk(source, followlinks=False):
            for name in dirs:
                no_links(Path(directory)/name)
            for name in sorted(names):
                p=no_links(Path(directory)/name); s=p.stat()
                assert stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_dev == ROOT.stat().st_dev
                assert name not in ('.env', 'id_rsa', 'id_ed25519') and '.ssh' not in p.parts
                total += s.st_size
                assert total <= CAP and len(entries) < 50000
                h=sha(p)
                if relative == SOURCES[0]: assert h == WHEEL_SHA[name]
                entries.append({'source':str(p), 'target':str(DEST/p.relative_to(ROOT/'.local')),
                                'bytes':s.st_size, 'sha256':h, 'mode':stat.S_IMODE(s.st_mode),
                                'mtime_ns':s.st_mtime_ns,'inode':s.st_ino,'source_dev':s.st_dev})
    assert {Path(e['source']).name for e in entries if '/diagnostic-wheels/' in e['source']} == set(WHEEL_SHA)
    plan={'kind':'authorized administrative relocation; not experiment', 'date':'2026-11-26 Asia/Shanghai',
          'authorization':'user: 可以复用hdd或将部分文档迁移，保持ssd空间充盈。',
          'source_roots':list(SOURCES), 'destination':str(DEST), 'total_bytes':total,
          'file_count':len(entries),'quota_before':before_quota,'protected_SHA_before':before,
          'entries':entries, 'model_calls':0,'service_changes':0}
    write_new(DEST/'migration_plan.json',plan)
    for e in entries:
        p=Path(e['source']); target=no_links(Path(e['target']))
        target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
        s=p.stat()
        assert (s.st_ino,s.st_mtime_ns,s.st_size)==(e['inode'],e['mtime_ns'],e['bytes']) and sha(p)==e['sha256']
        with p.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src,dst,1024*1024); dst.flush(); os.fsync(dst.fileno())
        os.chmod(target,e['mode']); os.utime(target, ns=(s.st_atime_ns,e['mtime_ns']))
        assert target.stat().st_size==e['bytes'] and sha(target)==e['sha256']
        sync_dir(target.parent)
    assert protected()==before
    write_new(DEST/'copy_verified.json',{'all_copies_SHA_verified':True,'files':len(entries),
                                       'bytes':total,'plan_sha256':sha(DEST/'migration_plan.json')})
    # Small durable pointer in each original ignored directory; future sync may
    # create new backup batches here. No symlink and no active source relocation.
    for relative in SOURCES:
        write_new(ROOT/relative/'ARCHIVED_HDD_20261126.json',{
            'archive':str(DEST), 'plan_sha256':sha(DEST/'migration_plan.json'),
            'original_root':str(ROOT/relative),'rollback':'restore only absent source paths after verifying each HDD SHA; never overwrite'})
    with (DEST/'removal_journal.jsonl').open('x',encoding='utf-8') as journal:
        for e in entries:
            p=no_links(Path(e['source'])); s=p.stat()
            assert (s.st_ino,s.st_mtime_ns,s.st_size)==(e['inode'],e['mtime_ns'],e['bytes'])
            assert sha(p)==e['sha256'] and sha(e['target'])==e['sha256']
            p.unlink(); sync_dir(p.parent)
            journal.write(json.dumps({'source_removed':e['source'],'verified_HDD':e['target'],'sha256':e['sha256']})+'\n')
            journal.flush(); os.fsync(journal.fileno())
    assert protected()==before
    after_quota=quota()
    receipt={'status':'completed','kind':'administrative migration, not test','files':len(entries),
             'bytes_retained_on_HDD':total,'all_target_SHA_verified':True,
             'all_original_source_copies_removed':all(not Path(e['source']).exists() for e in entries),
             'protected_files_unchanged':len(before),'quota_before':before_quota,'quota_after':after_quota,
             'elapsed_seconds':time.monotonic()-start,'plan':str(DEST/'migration_plan.json'),
             'plan_sha256':sha(DEST/'migration_plan.json'),'model_calls':0,'service_changes':0,
             'source_parent_directories_retained':True,'git_commit_or_push':False}
    write_new(DEST/'migration_receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__ == '__main__':
    try: main()
    except BaseException as exc:
        failure={'status':'failed','error_type':type(exc).__name__,'error':str(exc),
                 'elapsed_seconds':time.monotonic()-start,'destination':str(DEST),
                 'recovery':'all copied bytes and copy/plan manifests retained; do not rerun automatically'}
        if DEST.is_dir() and not (DEST/'migration_failure.json').exists():
            write_new(DEST/'migration_failure.json',failure)
        print(json.dumps(failure),flush=True)
        raise
