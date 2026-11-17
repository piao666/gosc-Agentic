"""Local management transport; no compute or model execution."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[3]
here=Path(__file__).resolve().parent
p=subprocess.run([sys.executable,str(root/'scripts/sync_hpc.py')],cwd=root,
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(here/'final_source_sync_stdout.txt').write_bytes(p.stdout)
(here/'final_source_sync_stderr.txt').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'))
print(p.stderr.decode(errors='replace'),file=sys.stderr)
raise SystemExit(p.returncode)
