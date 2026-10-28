"""Read-only SSH management, not local project computation."""
import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
old = root / 'research/logs/information-identifiability-acceptance-2026-10-27/manage_hpc.py'
spec = importlib.util.spec_from_file_location('prior_hpc_management', old)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.remote_script(module.PREFLIGHT)
out = Path(__file__).resolve().parent
(out/'preflight-stdout.txt').write_bytes(result.stdout)
(out/'preflight-stderr.txt').write_bytes(result.stderr)
if result.returncode:
    raise SystemExit(result.returncode)
data = json.loads(result.stdout.decode('utf-8').strip().splitlines()[-1])
(out/'preflight.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
data.pop('git_status',None)
print(json.dumps(data))
