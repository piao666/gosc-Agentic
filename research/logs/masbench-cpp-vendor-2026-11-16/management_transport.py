"""Local management-only SSH input/output transport; no local project compute."""
from pathlib import Path
import subprocess
import sys

here=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve()
prefix=sys.argv[2]
if source.parent not in {here,here.parent/'masbench-context-deployment-2026-11-16'}:
    raise RuntimeError('management script outside known task logs')
if '/' in prefix or '\\' in prefix or '..' in prefix: raise RuntimeError('prefix')
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc',
    '/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -'],
    input=source.read_bytes().replace(b'\r\n',b'\n'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55)
(here/(prefix+'.json')).write_bytes(p.stdout)
(here/(prefix+'_stderr.txt')).write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'))
print(p.stderr.decode(errors='replace'),file=sys.stderr)
raise SystemExit(p.returncode)
