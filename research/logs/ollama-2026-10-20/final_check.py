"""Read-only post-deployment checks; no additional inference."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from hpc_runs import ROOT,require_hpc,resource_limits,write_json
require_hpc()
out=Path(os.environ['GOSC_OUTPUT_DIR'])
settings=json.loads((ROOT/'.local/reproduction-services.json').read_text())
assert settings['version']=='0.11.11' and len(settings['models'])==3
assert all(m['full_gpu'] and m['integration']['calls']==1 and m['integration']['cache_hits']==0 for m in settings['models'])
def api(path):
    with urllib.request.urlopen(settings['ollama_base_url']+path,timeout=10) as response:return json.load(response)
version=api('/api/version');tags=api('/api/tags');loaded=api('/api/ps')
assert version['version']=='0.11.11'
assert {m['name'] for m in tags['models']}=={'qwen2.5:3b','qwen2.5:7b','llama3.2:3b'}
service=json.loads((ROOT/'.local/ollama/service.json').read_text())
assert Path('/proc/'+str(service['pid'])+'/cmdline').read_bytes().split(b'\0')[0].decode()==service['binary']
protected_changes=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only','--','gosc','experiments','tests','results','LICENSE']).decode().strip()
assert protected_changes==''
parent=ROOT.parents[1]
assert not (parent/'Github--llm').exists() and not (parent/'HM').exists()
assert (parent/'models').is_dir() and ROOT.is_dir()
lines=(ROOT/'.local/ollama/service.log').read_text(errors='replace').splitlines()
selected=[line for line in lines if any(marker in line for marker in ['inference compute','offloaded','Listening on 127.0.0.1'])]
(out/'gpu_service_evidence.log').write_text('\n'.join(selected)+'\n')
value={'status':'verified','service':service,'api_version':version,'tags':tags,'currently_loaded':loaded,
       'model_checks':settings['models'],'resources':resource_limits(),'protected_upstream_diff':protected_changes,
       'user_authorized_deletions_absent':True,'current_project_and_shared_models_preserved':True,
       'disk_allocations':subprocess.check_output(['du','-sxB1',str(ROOT/'.local/ollama'),str(parent/'models/ollama-gosc')]).decode(),
       'scientific_missions_in_this_deployment':0,'training_started':False,
       'scope':'Readiness and protection checks; no full live-LLM reproduction claim'}
write_json(out/'final_environment.json',value)
print(json.dumps(value,indent=2))
