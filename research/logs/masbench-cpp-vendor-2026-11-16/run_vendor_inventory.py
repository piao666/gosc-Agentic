"""Local file/SSH transport for the fixed small source inventory."""
from pathlib import Path
import json
import subprocess
import sys

here=Path(__file__).resolve().parent
root=here.parents[2]
lock=json.loads((root/'research/protocols/masbench_vendor_source_lock_2026-11-16.json').read_text())
source=(here/'vendor_source_inventory.py').read_text()
source=source.replace('lock=SOURCE_LOCK','lock='+repr(lock),1)
try:
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc',
  '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -'],
  input=source.replace('\r\n','\n').encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
except subprocess.TimeoutExpired as e:
 (here/'vendor_inventory_timeout_stdout.txt').write_bytes(e.stdout or b'')
 (here/'vendor_inventory_timeout_stderr.txt').write_bytes(e.stderr or b'')
 (here/'vendor_inventory_timeout.json').write_text(json.dumps({'kind':'management_ssh_timeout','seconds':120,'third_party_code_executed':False})+'\n')
 raise
(here/'vendor_inventory.json').write_bytes(p.stdout)
(here/'vendor_inventory_stderr.txt').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
raise SystemExit(p.returncode)
