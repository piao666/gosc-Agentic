"""Local SSH/file management only; no local scientific computation."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOG = Path(__file__).resolve().parent
path = ROOT/'research/logs/information-identifiability-acceptance-2026-10-27/manage_hpc.py'
spec = importlib.util.spec_from_file_location('previous_hpc_management', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = module.PREFLIGHT.replace("git_status=git('status','--short')",
    "timeout_program=__import__('shutil').which('timeout'),git_status=git('status','--short')")
result = module.remote_script(source)
attempt = 1
while (LOG/('preflight-attempt'+str(attempt)+'-stdout.txt')).exists():
    attempt += 1
(LOG/('preflight-attempt'+str(attempt)+'-stdout.txt')).write_bytes(result.stdout)
(LOG/('preflight-attempt'+str(attempt)+'-stderr.txt')).write_bytes(result.stderr)
if result.returncode:
    raise SystemExit(result.returncode)
data = json.loads(result.stdout.decode('utf-8').strip().splitlines()[-1])
(LOG/'preflight.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
data.pop('git_status', None)
print(json.dumps(data))
