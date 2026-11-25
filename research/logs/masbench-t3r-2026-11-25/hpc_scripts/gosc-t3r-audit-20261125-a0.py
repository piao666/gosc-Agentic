"""T3-R offline auditor. Standard library only; no network or model execution.

Run on HPC through hpc_runs.py. Historical sources are opened O_NOATIME and
O_NOFOLLOW. Writes are restricted to the new registered output directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import stat
import time

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
OLD = ROOT/'research/sync/runs/hpc-masbench-t3-live-20261125'
HDD = Path('/hdd/u202520081000097/gosc-t3-runs/hpc-masbench-t3-live-20261125')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(obj):
    return sha(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def read(path):
    path = Path(path)
    for parent in [*reversed(path.parents), path]:
        if parent.is_symlink():
            raise RuntimeError('symlink: '+str(parent))
    before = path.stat()
    fd = os.open(path, os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        raw = stream.read()
    after = path.stat()
    if (before.st_atime_ns, before.st_mtime_ns, before.st_ctime_ns, before.st_size) != (
            after.st_atime_ns, after.st_mtime_ns, after.st_ctime_ns, after.st_size):
        raise RuntimeError('source metadata changed: '+str(path))
    return raw


def load(path):
    return json.loads(read(path))


def walk(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOATIME | os.O_NOFOLLOW)
    try:
        names = sorted(os.listdir(fd))
    finally:
        os.close(fd)
    for name in names:
        child = path/name
        mode = child.lstat().st_mode
        if stat.S_ISDIR(mode):
            yield from walk(child)
        else:
            yield child


def write(name, value):
    out = Path(os.environ['GOSC_OUTPUT_DIR']).resolve()
    if out.parent.name.startswith('hpc-masbench-t3r-') is False:
        raise RuntimeError('new T3-R output directory required')
    target = out/name
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def chain(raw):
    rows = [json.loads(line) for line in raw.rstrip(b'\0\n ').splitlines() if line.strip()]
    previous = '0'*64
    for i, row in enumerate(rows):
        # Shape and canonical-chain formula are checked after inspection.
        if 'seq' in row and row['seq'] != i:
            raise RuntimeError('chain sequence')
    return rows


def inventory():
    manifest_raw = read(OLD/'outputs/hdd_manifest.json')
    manifest = json.loads(manifest_raw)
    expected = {e['path']: e for e in manifest['files']}
    anomalies = []
    if len(expected) != len(manifest['files']):
        anomalies.append({'kind':'duplicate_manifest_path'})
    actual = {p.relative_to(HDD).as_posix():p for p in walk(HDD)}
    rows, cache = [], {}
    for name, item in expected.items():
        rel = PurePosixPath(name)
        row = dict(item, exists=name in actual)
        safe = not (rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name)
        row['safe_path'] = safe
        if not safe or name not in actual:
            anomalies.append({'kind':'unsafe_or_missing','path':name}); rows.append(row); continue
        p = actual[name]
        row['regular_file'] = stat.S_ISREG(p.lstat().st_mode)
        if not row['regular_file']:
            anomalies.append({'kind':'non_regular','path':name}); rows.append(row); continue
        try:
            raw = read(p)
            row.update(readable=True, actual_size=len(raw), actual_sha256=sha(raw),
                       size_match=len(raw)==item['size'], sha_match=sha(raw)==item['sha256'],
                       source_timestamps_preserved=True)
            suffix = p.suffix
            if suffix == '.json':
                value = json.loads(raw); row['content_type'] = 'JSON'; cache[name] = value
            elif suffix == '.jsonl':
                value = chain(raw); row['content_type'] = 'JSONL'; row['records'] = len(value); cache[name] = value
            else:
                raw.decode('utf-8'); row['content_type'] = 'UTF-8 text'
            if not row['size_match'] or not row['sha_match']:
                anomalies.append({'kind':'byte_or_sha_mismatch','path':name})
        except Exception as exc:
            row['error'] = type(exc).__name__+': '+str(exc)
            anomalies.append({'kind':'read_or_type_error','path':name,'error':row['error']})
        rows.append(row)
    extra = sorted(set(actual)-set(expected))
    for name in extra:
        anomalies.append({'kind':'extra','path':name})
    result = {'schema_version':1,'generation':'audit_t3r.py inventory; O_NOATIME/O_NOFOLLOW; stdlib only',
              'hdd_root':str(HDD),'manifest_source':str(OLD/'outputs/hdd_manifest.json'),
              'manifest_sha256':sha(manifest_raw),'expected_files':len(manifest['files']),
              'actual_entries':len(actual),'read_files':sum(r.get('readable',False) for r in rows),
              'sha_pass':sum(r.get('sha_match',False) for r in rows),
              'size_pass':sum(r.get('size_match',False) for r in rows),
              'expected_bytes':manifest['bytes'],'actual_listed_bytes':sum(r.get('actual_size',0) for r in rows),
              'anomalies':anomalies,'files':rows,'new_model_calls':0,'raw_text_exported':False}
    write('evidence_inventory.json',result)
    # Shape-only exploratory index. No private text is copied.
    shapes=[]
    for name,value in cache.items():
        if any(x in name for x in ('application-result','provider-request','wire-events')) or name.endswith('ledger.jsonl'):
            shapes.append({'path':name,'shape':list(value) if isinstance(value,dict) else list(value[0]) if value else [],
                           'nested':{k:list(v) if isinstance(v,dict) else ('list '+str(len(v))) if isinstance(v,list) else type(v).__name__
                                     for k,v in value.items()} if isinstance(value,dict) else {}})
    write('source_shapes.json',shapes)
    print(json.dumps({k:v for k,v in result.items() if k!='files'}))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['inventory'])
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    if os.getuid()!=8301880:
        raise RuntimeError('unexpected UID')
    start=time.monotonic()
    inventory()
    print(json.dumps({'wall_seconds':time.monotonic()-start,'usage':list(resource.getrusage(resource.RUSAGE_SELF))}))


if __name__=='__main__':
    main()
