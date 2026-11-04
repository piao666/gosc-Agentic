"""Remove only the explicitly approved completed archive after full SHA verification."""
import datetime
import hashlib
import json
import os
from pathlib import Path

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
target=root/'.local/ollama/downloads/ollama-linux-amd64-0.11.11.tgz'
assert os.getuid()==8301880 and target.is_file() and not target.is_symlink()
assert target.resolve()==target and target.stat().st_uid==os.getuid()
assert target.stat().st_size==1908755362
expected='1d2988c29346e6af0216c847db20f7df7794412ae56674eeec21e0917113843f'
with target.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
assert actual==expected,'Unexpected archive identity: preserve'
runtime=root/'.local/ollama/runtime/0.11.11/bin/ollama'
partial=target.with_name('ollama-linux-amd64-0.11.11-hpc-direct.partial.tgz')
assert runtime.is_file() and partial.is_file()
out=Path(os.environ['GOSC_OUTPUT_DIR'])
before={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target':str(target),
        'size':target.stat().st_size,'allocated_before':target.stat().st_blocks*512,'sha256':actual,
        'authorization':'User approved this completed archive deletion and a new 30-minute remaining-model maintenance window'}
(out/'archive_before.json').write_text(json.dumps(before,indent=2)+'\n')
target.unlink()
after={**before,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'archive_exists_after':target.exists(),'runtime_exists_after':runtime.is_file(),
       'old_failed_partial_exists_after':partial.is_file()}
(out/'archive_after.json').write_text(json.dumps(after,indent=2)+'\n')
print(json.dumps(after))
