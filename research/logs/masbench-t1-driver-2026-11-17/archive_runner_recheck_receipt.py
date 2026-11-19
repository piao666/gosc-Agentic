"""Write a verified gzip copy of this turn's receipt after its raw upload failed."""
import base64
import gzip
import hashlib
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
name = '20261118T080840Z-e03b60.json'
data = (root/'research/sync/receipts'/name).read_bytes()
sha = hashlib.sha256(data).hexdigest()
assert sha=='1de8d67965067cc8eee784ad2ac0581d87318ddbcbae4777a7ceece55f879351'
packed = gzip.compress(data,compresslevel=9,mtime=0)
archive = root/'.local'/f'{name}.gz'
with archive.open('xb') as out:
    out.write(packed)

source = '''
from pathlib import Path
import base64,gzip,hashlib,json,os
root = Path('/home/u202520081000097/jupyterlab/Paper/gosc/research/sync/receipts')
original = root / %r
packed = base64.b64decode(%r)
sha = %r
assert original.is_file() and not original.is_symlink() and original.stat().st_size==0
assert hashlib.sha256(gzip.decompress(packed)).hexdigest()==sha
archive = original.with_suffix('.json.gz')
with archive.open('xb') as target:
    target.write(packed)
    target.flush()
    os.fsync(target.fileno())
assert archive.read_bytes()==packed
print(json.dumps({'archive':archive.name,'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest(),
                  'original_sha256':sha,'failed_raw_upload_preserved':True}))
''' % (name, base64.b64encode(packed), sha)
command = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','hpc',
    '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -']
subprocess.run(command,input=source.encode(),check=True,timeout=30)
