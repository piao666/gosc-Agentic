"""Check retained writes and readback on the project SSD after verified cleanup."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

ROOT = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
ARCHIVE = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
UID = 8301880
assert os.getuid()==UID and ROOT.resolve()==ROOT and ARCHIVE.resolve()==ARCHIVE
journal = ARCHIVE/'ssd_cleanup_execution_2026-11-19.jsonl'
rows = [json.loads(line) for line in journal.read_text().splitlines()]
summary, = [row for row in rows if row['kind']=='summary']
assert summary['complete'] and len(summary['removed'])==4
assert all(not Path(row['path']).exists() for row in summary['removed'])

expected = hashlib.sha256()
samples = []
started = time.monotonic()
with tempfile.TemporaryDirectory(dir=ROOT/'.local',prefix='t1-sustained-write-20261119-') as scratch:
    target = Path(scratch)/'retained.bin'
    for value in (1,2,3):
        block = bytes([value])*1024**2
        with target.open('ab') as writer:
            for _ in range(16):
                writer.write(block)
                expected.update(block)
            writer.flush()
            os.fsync(writer.fileno())
        with target.open('rb') as reader:
            observed = hashlib.file_digest(reader,'sha256').hexdigest()
        info = target.stat()
        assert info.st_size==value*16*1024**2 and info.st_blocks*512>=info.st_size and observed==expected.hexdigest()
        samples.append({'utc':datetime.now(timezone.utc).isoformat(),'retained_bytes':info.st_size,
                        'allocated_bytes':info.st_blocks*512,'sha256':observed,
                        'elapsed_seconds':round(time.monotonic()-started,3)})
        if value<3:
            time.sleep(5)
    receipt = Path(scratch)/'write-check.json'
    with receipt.open('x') as stream:
        json.dump(samples,stream)
        stream.flush()
        os.fsync(stream.fileno())
    assert json.loads(receipt.read_bytes())==samples
assert not target.exists() and not receipt.exists()
print(json.dumps({'host':os.uname().nodename,'project':str(ROOT),'samples':samples,
                  'quota_probe_scratch_removed':True,'execution_seconds':round(time.monotonic()-started,3)}))
