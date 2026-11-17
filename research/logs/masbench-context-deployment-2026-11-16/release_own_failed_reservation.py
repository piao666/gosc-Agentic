"""Local transport for reclaiming only this run's failed quota placeholder."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from hpc_runs import remote_script

source=r'''
from pathlib import Path
import json,os
r=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880
run=r/'research/sync/runs/hpc-masbench-context-build-v2-20261116'
s=json.loads((run/'status.json').read_text())
b=json.loads((run/'outputs/build.json').read_text())
assert s['status']=='failed' and b['official_download_payload_bytes']==0
assert b['error']=='OSError: [Errno 122] Disk quota exceeded'
p=r/'.local/masbench-exact-context/hpc-masbench-context-build-v2-20261116/quota-reservation'
assert p.resolve()==p and not p.is_symlink() and p.stat().st_uid==8301880
st=p.stat();assert st.st_size==4294967296
before={'logical_bytes':st.st_size,'allocated_bytes':st.st_blocks*512}
with p.open('r+b') as f:f.truncate(0);os.fsync(f.fileno())
after=p.stat()
print(json.dumps({'path':str(p),'before':before,'after':{'logical_bytes':after.st_size,'allocated_bytes':after.st_blocks*512},
 'only_own_failed_placeholder_reclaimed':True,'historical_run_modified':False,
 'other_projects_models_or_results_deleted':False}))
'''
p=remote_script(source)
(HERE/'own_reservation_reclaimed.json').write_bytes(p.stdout)
(HERE/'own_reservation_reclaimed_stderr.txt').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'))
print(p.stderr.decode(errors='replace'),file=sys.stderr)
raise SystemExit(p.returncode)
