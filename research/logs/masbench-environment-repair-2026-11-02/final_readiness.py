"""HPC registered metadata/client acceptance only. No chat, generate, model load or task."""
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import urllib.request

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.name=='posix' and os.getuid()==8301880 and root.is_dir()
import openai
base='http://127.0.0.1:11434'
def api(path,body=None):
    request=urllib.request.Request(base+path,None if body is None else json.dumps(body).encode(),
                                   {'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
def read(path):return json.loads(path.read_text())
restore=read(root/'research/sync/runs/hpc-masbench-model-restore-after-storage-retry1-20261102/outputs/models_ready.json')
expected=set(restore['models'])
client=openai.OpenAI(api_key='ollama-local-placeholder',base_url=base+'/v1',max_retries=0,timeout=15)
try:listed=client.models.list();ids={item.id for item in listed.data}
finally:client.close()
assert ids==expected,(ids,expected)
details={}
for name in sorted(expected):
    value=api('/api/show',{'model':name})
    info=value.get('model_info',{})
    details[name]={'details':value.get('details'),
                   'declared_context_fields':{k:v for k,v in info.items() if k.endswith('.context_length')},
                   'template_sha256':hashlib.sha256(value.get('template','').encode()).hexdigest(),
                   'license_sha256':hashlib.sha256(value.get('license','').encode()).hexdigest()}
assert not api('/api/ps').get('models')
environment=root/'.local/envs/masbench-reasoning-v1'
value={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':str(environment),
       'python':str(environment/'bin/python'),'endpoint':base+'/v1','service_version':api('/api/version'),
       'model_ids_via_openai_sdk':sorted(ids),'model_metadata':details,
       'model_manifest_sha256':{k:v['manifest_sha256'] for k,v in restore['models'].items()},
       'packages':{d.metadata['Name']:d.version for d in metadata.distributions()},
       'scope':'Restored files, packages and metadata transport only; model loading and Reasoning capability Pending',
       'inference_requested':False,'model_load_requested':False,'benchmark_executed':False,
       'original_context_default_changed':False}
target=environment/'gosc_readiness.json'
assert not target.exists(),'Preserve existing readiness rather than overwriting'
text=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
target.write_text(text)
(Path(os.environ['GOSC_OUTPUT_DIR'])/'environment_ready.json').write_text(text)
print(json.dumps({'model_ids':sorted(ids),'sdk_model_listing':'passed','show_metadata':'passed',
                  'inference_requested':False,'model_load_requested':False}))
