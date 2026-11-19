"""Retire only the four verified SSD copies explicitly confirmed by the user."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
RUNS = ROOT/'research/sync/runs'
ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
MANIFEST_SHA = 'b6dc850df47ece3f5929bf6c6f83f5c2fb08ef9d8c37ee3b3b5f6b1338bb5d17'
UID = 8301880
CONFIRMED = {
    'resume-radio-noise-20261020/outputs/pool-001-jobs.jsonl':
        'd23f11042f80753c261b3dec52b2305fc52478388916471f61de537da166f850',
    'resume-radio-noise-20261020/outputs/legacy_results/noise.jsonl':
        '4c177982d2c7533218865a71b32431f1a1ab2de7feb29619313ce77dfddf5a97',
    'resume-radio-overhead-20261020/outputs/pool-001-jobs.jsonl':
        '3d7d647eb61be3942c9939e05f61f7348bc8ed6efd8c8e255c13d2370f7bdb15',
    'resume-radio-overhead-20261020/outputs/legacy_results/overhead.jsonl':
        '1dac0d00c43d78df88d6278007d275b35ceb2731fad6bbb6d34953088742b7bf',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def sync_dir(path):
    fd = os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    sync_dir(path.parent)


def no_active_tasks(targets):
    for p in RUNS.glob('*/status.json'):
        assert json.loads(p.read_bytes())['status'] not in ('planned','running'),str(p)
    inaccessible = []
    for proc in Path('/proc').iterdir():
        try:
            if not proc.name.isdigit() or proc.stat().st_uid!=UID:
                continue
            for fd in (proc/'fd').iterdir():
                try:
                    assert str(fd.readlink()) not in targets,f'active open SSD file in PID {proc.name}'
                except (FileNotFoundError, ProcessLookupError):
                    continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            inaccessible.append(proc.name)
    return inaccessible


def identity(path, row):
    info = path.lstat()
    assert path.resolve()==path and stat.S_ISREG(info.st_mode) and info.st_uid==UID
    assert (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink)==(
        row['ssd_device'],row['ssd_inode'],row['size'],row['ssd_mtime_ns'],1)
    return info


assert os.getuid()==UID and os.uname().nodename=='n1' and ROOT.resolve()==ROOT and ARCHIVE.resolve()==ARCHIVE
assert ROOT.stat().st_dev!=ARCHIVE.stat().st_dev
assert sha(ARCHIVE/'archive_manifest.json')==MANIFEST_SHA
manifest = json.loads((ARCHIVE/'archive_manifest.json').read_bytes())
approval = json.loads((ARCHIVE/'ssd_cleanup_candidates.json').read_bytes())
verification = json.loads((ARCHIVE/'readback_verification.json').read_bytes())
rows = approval['files']
assert approval['source_root']==str(ROOT) and approval['archive']==str(ARCHIVE)
assert rows==manifest['proposed_ssd_cleanup'] and len(rows)==len(CONFIRMED)
assert verification['archive_manifest_sha256']==MANIFEST_SHA
verified = {row['path']:row['sha256'] for row in verification['restore_drill_files'] if row['matches_ssd']}
prefix = 'research/sync/runs/'
assert {row['path']:row['sha256'] for row in rows}==verified=={prefix+p:h for p,h in CONFIRMED.items()}
targets = {str(ROOT/row['path']) for row in rows}
inaccessible = no_active_tasks(targets)
allocated = 0
for row in rows:
    source = ROOT/row['path']
    backup = ARCHIVE/row['path']
    assert backup.resolve()==backup and backup.stat().st_size==row['size']
    assert sha(source)==sha(backup)==row['sha256']
    allocated += identity(source,row).st_blocks*512
    run = RUNS/Path(row['path']).parts[3]
    state = json.loads((run/'status.json').read_bytes())
    assert state==manifest['runs'][run.name] and state['status']=='completed'
    indexed = {i['path']:i for i in json.loads((run/'artifacts.json').read_bytes())['files']}
    assert indexed[source.relative_to(run).as_posix()]['sha256']==row['sha256']

journal = ARCHIVE/'ssd_cleanup_execution_2026-11-19.jsonl'
record = {'user_confirmation':'确认','confirmation_scope':'the four SSD filenames in the archive report',
          'started_utc':utc(),'host':os.uname().nodename,'archive':str(ARCHIVE),
          'archive_manifest_sha256':MANIFEST_SHA,'candidate_allocated_bytes':allocated,
          'unreadable_same_uid_fd_tables':inaccessible,'files':rows}
assert journal.is_file() and not journal.is_symlink()
previous, = [json.loads(line) for line in journal.read_text().splitlines()]
assert previous['kind']=='preverified' and previous['files']==rows
locators = []
for name in sorted(manifest['runs']):
    run = RUNS/name
    files = [r for r in rows if (ROOT/r['path']).is_relative_to(run)]
    value = {
        'intent':'references user-confirmed SSD copies retired from this run',
        'manifest_sha256':MANIFEST_SHA,'hdd_archive':str(ARCHIVE),
        'hdd_execution_journal':str(journal),'files':files,
        'restore_note':'Copy archived file to original relative path and verify SHA-256 before use.',
    }
    location = run/'ssd_archive_location.json'
    save(ARCHIVE/f'{name}.ssd_archive_location.json',value)
    if location.exists():
        assert location.resolve()==location and location.stat().st_size==0
        failed_copy = ARCHIVE/f'{name}.ssd_locator_before_space_recovery.empty'
        with failed_copy.open('xb') as backup:
            backup.write(location.read_bytes())
            backup.flush()
            os.fsync(backup.fileno())
    locators.append((location,value))

with journal.open('a',encoding='utf-8') as out:
    def log(event):
        out.write(json.dumps(event)+'\n')
        out.flush()
        os.fsync(out.fileno())

    log(dict(record,kind='preverified_retry',previous_error='SSD locator write EDQUOT; zero files retired'))
    sync_dir(journal.parent)
    no_active_tasks(targets)
    removed = []
    try:
        for row in rows:
            path = ROOT/row['path']
            blocks = identity(path,row).st_blocks*512
            log({'kind':'unlink-intent','path':str(path),'utc':utc()})
            path.unlink()
            removed.append({'path':str(path),'size':row['size'],'allocated_bytes':blocks,'sha256':row['sha256']})
            sync_dir(path.parent)
            assert not path.exists()
            log({'kind':'unlink-verified','file':removed[-1],'utc':utc()})
    finally:
        log({'kind':'summary','removed':removed,'complete':len(removed)==len(rows),'utc':utc()})
    assert len(removed)==4
    locator_error = None
    try:
        for location,value in locators:
            if location.exists():
                assert location.stat().st_size==0
                with location.open('r+b') as dest:
                    dest.write((json.dumps(value,indent=2)+'\n').encode())
                    dest.flush()
                    os.fsync(dest.fileno())
                sync_dir(location.parent)
            else:
                save(location,value)
            assert json.loads(location.read_bytes())==value
    except OSError as exc:
        locator_error = repr(exc)
    log({'kind':'ssd_locator_write','error':locator_error,'utc':utc()})
print(json.dumps(dict(record,removed=removed,completed_utc=utc(),hdd_execution_journal=str(journal),
                      ssd_locator_error=locator_error)))
