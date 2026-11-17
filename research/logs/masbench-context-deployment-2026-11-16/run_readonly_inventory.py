"""Local SSH transport only; remote input is UTF-8/LF and is read-only."""
from pathlib import Path
import subprocess

here = Path(__file__).resolve().parent
payload = (here/'readonly_inventory.py').read_bytes().replace(b'\r\n',b'\n')
p = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc',
    '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -'],
    input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=50)
(here/'readonly_inventory.json').write_bytes(p.stdout)
(here/'readonly_inventory_stderr.txt').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'))
print('ssh_exit_code='+str(p.returncode))
raise SystemExit(p.returncode)
