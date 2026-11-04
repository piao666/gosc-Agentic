"""Bounded metadata-only diagnosis; no credentials, weights, inference or mutations on HPC."""
import datetime
import json
from pathlib import Path
import subprocess

LOG=Path(__file__).resolve().parent
REMOTE=r'''
import datetime,json,os,shutil,subprocess,urllib.request
from pathlib import Path
home=Path.home();root=home/'jupyterlab/Paper/gosc'
def get(path):
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434'+path,timeout=3) as response:return json.load(response)
    except Exception as error:return {'error':type(error).__name__}
def storage(path):
    row={'path':str(path),'resolved':str(path.resolve()),'exists':path.is_dir()}
    if path.is_dir():
        row['children']=[p.name for p in sorted(path.iterdir())][:30]
        manifests=path/'manifests';blobs=path/'blobs'
        if manifests.is_dir():
            files=[p for p in manifests.glob('*/*/*/*') if p.is_file()]
            row['manifests']=[{'path':str(p.relative_to(path)),'bytes':p.stat().st_size} for p in files[:50]]
        if blobs.is_dir():
            files=[p for p in blobs.iterdir() if p.is_file()]
            row['blob_count']=len(files);row['declared_file_bytes']=sum(p.stat().st_size for p in files)
            row['largest_blob_metadata']=[{'name':p.name,'bytes':p.stat().st_size} for p in sorted(files,key=lambda p:p.stat().st_size,reverse=True)[:8]]
    return row
processes=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        name=(p/'comm').read_text().strip()
        if name!='ollama':continue
        env=dict(item.split('=',1) for item in (p/'environ').read_bytes().decode(errors='replace').split('\0') if '=' in item)
        processes.append({'pid':int(p.name),'uid':p.stat().st_uid,'exe':os.readlink(p/'exe'),
            'allowed_environment':{k:env.get(k) for k in ['OLLAMA_MODELS','OLLAMA_HOST','OLLAMA_NUM_PARALLEL','OLLAMA_MAX_LOADED_MODELS','OLLAMA_CONTEXT_LENGTH','OLLAMA_NO_CLOUD']}})
    except (OSError,ValueError):pass
state=root/'.local/ollama/service.json'
service={}
if state.is_file():
    data=json.loads(state.read_text());service={k:data.get(k) for k in ['pid','binary','bind','models','version','started_at_unix']}
model_parent=home/'jupyterlab/models'
running=[]
for p in (root/'research/sync/runs').glob('*/status.json'):
    data=json.loads(p.read_text())
    if data.get('status')=='running':running.append({'run_id':p.parent.name,'pid':data.get('pid')})
quota={'available':bool(shutil.which('quota'))}
if quota['available']:
    p=subprocess.run(['quota','-s'],capture_output=True,text=True,timeout=10)
    quota.update(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
print(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uid':os.getuid(),
    'processes':processes,'service_state':service,'models_parent_children':[p.name for p in model_parent.iterdir()] if model_parent.is_dir() else [],
    'storage':[storage(p) for p in [model_parent/'ollama-gosc',home/'.ollama/models',root/'.local/ollama/models']],
    'ollama':{p:get(p) for p in ['/api/version','/api/tags','/api/ps']},'running_records':running,
    'quota':quota,'uv_path':str(home/'.local/bin/uv'),'uv_exists':(home/'.local/bin/uv').is_file(),
    'repair_env_exists':(root/'.local/envs/masbench-reasoning-v1').exists(),'inference_requested':False},ensure_ascii=False))
'''
command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc','/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -']
p=subprocess.run(command,input=REMOTE.encode(),capture_output=True,timeout=55)
(LOG/'diagnosis_stdout.json').write_bytes(p.stdout)
(LOG/'diagnosis_stderr.txt').write_bytes(p.stderr)
print(json.dumps({'exit_code':p.returncode,'inventory':json.loads(p.stdout) if p.returncode==0 else None},ensure_ascii=False))
