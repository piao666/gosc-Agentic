"""Preserve the registered local mirror and the observed SSD copy side by side."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN = 'research/sync/runs/hpc-masbench-t1b-runner-recheck-20261118'
ARTIFACT = 'outputs/driver/control.jsonl'
raw = (ROOT/RUN/ARTIFACT).read_bytes()
registered = next(e for e in json.loads((ROOT/RUN/'artifacts.json').read_bytes())['files'] if e['path']==ARTIFACT)
assert len(raw)==registered['size']==131072
assert hashlib.sha256(raw).hexdigest()==registered['sha256']=='8747c4d5ece54f50776ccaa1a29ddc830513f9a5082e2c23c02a85964867cfc3'
remote = r'''
from datetime import datetime, timezone
import base64,gzip,hashlib,json,os
from pathlib import Path
root = Path('/home/u202520081000097/jupyterlab/Paper/gosc')
hdd = Path('/hdd/u202520081000097/gosc-archive/2026-11-18-ssd-relief-v1')
run = root / RUN
archive = hdd / 't1_failed_run_control_versions_2026-11-19'
assert os.getuid()==8301880 and root.resolve()==root and hdd.resolve()==hdd
mirror = gzip.decompress(base64.b64decode(PAYLOAD))
ssd = (run/ARTIFACT).read_bytes()
expected = next(e for e in json.loads((run/'artifacts.json').read_bytes())['files'] if e['path']==ARTIFACT)
def sha(data):
    return hashlib.sha256(data).hexdigest()
assert len(mirror)==len(ssd)==expected['size']==131072
assert sha(mirror)==expected['sha256'] and sha(ssd)=='8e11ff18c2b3e6c017cbd1adfebe1fe86e9ad3b0728d03ab6968f69adefa6f69'
prefix = ssd.rstrip(b'\0')
complete = mirror.rstrip(b'\0')
assert complete.startswith(prefix) and prefix.endswith(b'\n')
extra = complete[len(prefix):].splitlines()
assert len(extra)==1
last = json.loads(extra[0])
assert last['seq']==21 and last['event']=={'kind':'charge','category':'cleanup_get'}
assert last['previous']==json.loads(prefix.splitlines()[-1])['hash']
archive.mkdir(mode=0o700)
def save(name,data):
    with (archive/name).open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    assert (archive/name).read_bytes()==data
save('registered_mirror.control.jsonl',mirror)
save('current_ssd.control.jsonl',ssd)
record = {'archive':str(archive),'utc':datetime.now(timezone.utc).isoformat(),
          'source_run':str(run),'registered_mirror_sha256':sha(mirror),'current_ssd_sha256':sha(ssd),
          'same_allocated_logical_bytes':len(ssd),'exact_prefix_match':True,
          'mirror_suffix':last,'remote_original_preserved':True}
save('comparison.json',(json.dumps(record,indent=2)+'\n').encode())
for folder in (archive,archive.parent):
    fd = os.open(folder,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
print(json.dumps(record))
'''
payload = base64.b64encode(gzip.compress(raw,mtime=0))
prefix = f'RUN={RUN!r}\nARTIFACT={ARTIFACT!r}\nPAYLOAD={payload!r}\n'
command = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','hpc',
           '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -']
result = subprocess.run(command,input=(prefix+remote).encode(),capture_output=True,timeout=25)
(HERE/'t1_control_version_preservation_20261119.json').write_bytes(result.stdout)
(HERE/'t1_control_version_preservation_20261119_stderr.txt').write_bytes(result.stderr)
print(result.stdout.decode())
if result.stderr:
    print(result.stderr.decode())
raise SystemExit(result.returncode)
