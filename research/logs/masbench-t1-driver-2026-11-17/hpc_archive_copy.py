"""Copy two finished run trees and their original receipts to the private HDD."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
HDD = Path('/hdd/u202520081000097')
ARCHIVE = HDD/'gosc-archive/2026-11-18-ssd-relief-v1'
RUNS = Path('research/sync/runs')
RECEIPTS = Path('research/sync/receipts')
PICKS = {
    'resume-radio-noise-20261020': ('outputs/pool-001-jobs.jsonl','outputs/legacy_results/noise.jsonl'),
    'resume-radio-overhead-20261020': ('outputs/pool-001-jobs.jsonl','outputs/legacy_results/overhead.jsonl'),
}
LATEST = '20261118T080840Z-e03b60.json.gz'
LATEST_RAW_SHA = '1de8d67965067cc8eee784ad2ac0581d87318ddbcbae4777a7ceece55f879351'
UID = 8301880


def required(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def stationary():
    active = []
    for p in (ROOT/RUNS).glob('*/status.json'):
        if json.loads(p.read_bytes())['status'] in ('running','planned'):
            active.append(p.parent.name)
    required(not active,f'active registered runs: {active}')


def registered_run(name):
    path = ROOT/RUNS/name
    state = json.loads((path/'status.json').read_bytes())
    required(state['run_id']==name and state['status']=='completed' and state['exit_code']==0,
             f'run is not completed: {name}')
    artifacts = {r['path']:r for r in json.loads((path/'artifacts.json').read_bytes())['files']}
    files = sorted(p for p in path.rglob('*') if not p.is_dir() or p.is_symlink())
    for p in files:
        s = p.lstat()
        required(stat.S_ISREG(s.st_mode) and p.resolve()==p and s.st_uid==UID,f'unsafe source: {p}')
    names = {p.relative_to(path).as_posix() for p in files}
    required(set(artifacts)<=names and set(PICKS[name])<=set(artifacts),f'missing registered outputs: {name}')
    required({'status.json','manifest.json','source_snapshot.json','artifacts.json','stdout.log','stderr.log'}<=names,
             f'missing registration files: {name}')
    return state, artifacts, files


def receipt_covers(receipt, selected):
    indexed = {row['path']:row for row in receipt.get('files',[]) if row['path'] in selected}
    return len(indexed)==len(selected) and all(
        row['sha256']==selected[name]['sha256'] and row['size']==selected[name]['size']
        and row.get('transfer_status') in ('copied','unchanged')
        for name,row in indexed.items())


def original_receipts(selection):
    first = {}
    for item in sorted((ROOT/RECEIPTS).glob('*.json')):
        if item.is_symlink() or item.stat().st_size<2:
            continue
        body = item.read_bytes()
        waiting = {name for name in selection if name not in first and name.encode() in body}
        if not waiting:
            continue
        receipt = json.loads(body)
        for name in sorted(waiting):
            if receipt_covers(receipt,selection[name]):
                first[name]=item
        if len(first)==len(selection):
            break
    required(len(first)==len(selection),'a complete original transfer receipt was not found')
    newest = ROOT/RECEIPTS/LATEST
    latest_raw = gzip.decompress(newest.read_bytes())
    required(hashlib.sha256(latest_raw).hexdigest()==LATEST_RAW_SHA,'latest receipt raw SHA mismatch')
    latest_obj = json.loads(latest_raw)
    required(all(receipt_covers(latest_obj,picked) for picked in selection.values()),'latest receipt incomplete')
    return first, newest


def copy_verified(source, target, registered=None):
    target.parent.mkdir(parents=True,exist_ok=True)
    writer = hashlib.sha256()
    fd = os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as reader, target.open('xb') as output:
        first = os.fstat(reader.fileno())
        required(stat.S_ISREG(first.st_mode) and first.st_uid==UID,f'unsafe opened source: {source}')
        for block in iter(lambda:reader.read(1024**2),b''):
            writer.update(block)
            output.write(block)
        last = os.fstat(reader.fileno())
        required((first.st_dev,first.st_ino,first.st_size,first.st_mtime_ns,first.st_ctime_ns)==
                 (last.st_dev,last.st_ino,last.st_size,last.st_mtime_ns,last.st_ctime_ns),f'source changed: {source}')
        output.flush()
        os.fsync(output.fileno())
    identity = writer.hexdigest()
    required(target.stat().st_size==first.st_size and digest(target)==identity,f'HDD readback mismatch: {target}')
    if registered is not None:
        required(registered['sha256']==identity and registered['size']==first.st_size,f'run hash mismatch: {source}')
    os.chmod(target,stat.S_IMODE(first.st_mode)&0o777)
    os.utime(target,ns=(first.st_atime_ns,first.st_mtime_ns))
    return {'path':source.relative_to(ROOT).as_posix(),'size':first.st_size,'sha256':identity,
            'ssd_allocated_bytes':first.st_blocks*512,'ssd_inode':first.st_ino,'ssd_link_count':first.st_nlink,
            'ssd_device':first.st_dev,'ssd_mtime_ns':first.st_mtime_ns}


def write_json(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


started = time.monotonic()
required(os.getuid()==UID and ROOT.resolve()==ROOT and HDD.resolve()==HDD and HDD.stat().st_uid==UID,'workspace identity')
required(ROOT.stat().st_dev!=HDD.stat().st_dev,'SSD and HDD must be distinct mounts')
stationary()
records = {name:registered_run(name) for name in PICKS}
selected = {
    name:{(RUNS/name/path).as_posix():records[name][1][path] for path in paths}
    for name,paths in PICKS.items()
}
first_receipts, final_receipt = original_receipts(selected)
receipt_sources = sorted(set(first_receipts.values()) | {final_receipt})
parent = ARCHIVE.parent
parent.mkdir(mode=0o700,exist_ok=True)
required(parent.resolve()==parent and parent.stat().st_uid==UID and not parent.stat().st_mode&0o077,'archive parent not private')
required(not ARCHIVE.exists(),'archive already published')
stage = ARCHIVE.with_name(ARCHIVE.name+'.copy-in-progress')
stage.mkdir(mode=0o700)
rows = []
for name,(state,index,files) in records.items():
    for source in files:
        relative = source.relative_to(ROOT)
        row = copy_verified(source,stage/relative,index.get(source.relative_to(ROOT/RUNS/name).as_posix()))
        rows.append(row)
    required(json.loads((ROOT/RUNS/name/'status.json').read_bytes())==state,f'run status changed: {name}')
for path in receipt_sources:
    rows.append(copy_verified(path,stage/path.relative_to(ROOT)))
stationary()
picks = {p for paths in selected.values() for p in paths}
cleanup = [row for row in rows if row['path'] in picks]
required(len(cleanup)==4 and all(r['ssd_link_count']==1 for r in cleanup),'cleanup candidate link count')
size = sum(r['ssd_allocated_bytes'] for r in cleanup)
metadata = {
    'archive':str(ARCHIVE),'source_root':str(ROOT),'host':os.uname().nodename,'uid':UID,
    'created_utc':datetime.now(timezone.utc).isoformat(),
    'runs':{name:record[0] for name,record in records.items()},
    'first_transfer_receipt':{name:p.relative_to(ROOT).as_posix() for name,p in first_receipts.items()},
    'latest_transfer_receipt':final_receipt.relative_to(ROOT).as_posix(),
    'latest_transfer_receipt_decoded_sha256':LATEST_RAW_SHA,
    'files':rows,'file_count':len(rows),'logical_bytes':sum(row['size'] for row in rows),
    'proposed_ssd_cleanup':cleanup,'estimated_ssd_release_bytes':size,
    'ssd_cleanup_done':False,'copy_elapsed_seconds':round(time.monotonic()-started,3),
}
write_json(stage/'archive_manifest.json',metadata)
write_json(stage/'ssd_cleanup_candidates.json',{'source_root':str(ROOT),'archive':str(ARCHIVE),
    'status':'awaiting_user_confirmation','files':cleanup,'estimated_ssd_release_bytes':size})
with (stage/'SHA256SUMS').open('x',encoding='utf-8') as stream:
    for row in sorted(rows,key=lambda r:r['path']):
        stream.write(f"{row['sha256']}  {row['path']}\n")
    stream.flush()
    os.fsync(stream.fileno())
stage.rename(ARCHIVE)
print(json.dumps(metadata))
