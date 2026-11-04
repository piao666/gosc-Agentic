"""Metadata of the three previously registered model manifests; no weight read or inference."""
import json
from pathlib import Path
import subprocess

LOG=Path(__file__).resolve().parent
REMOTE=r'''
import datetime,json
from pathlib import Path
base=Path('/home/u202520081000097/jupyterlab/models/ollama-gosc')
rows=[]
for model,tag in [('qwen2.5','3b'),('llama3.2','3b'),('qwen2.5','7b')]:
    p=base/'manifests/registry.ollama.ai/library'/model/tag
    row=dict(model=model+':'+tag,manifest_path=str(p),manifest_exists=p.is_file())
    if p.is_file():
        m=json.loads(p.read_text());row['manifest_bytes']=p.stat().st_size
        row['blobs']=[dict(digest=x['digest'],declared_size=x.get('size'),
            exists=(base/'blobs'/x['digest'].replace(':','-')).is_file()) for x in [m['config']]+m['layers']]
    rows.append(row)
print(json.dumps(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),models_root_exists=base.is_dir(),
    models=rows,scope='Manifest metadata and blob existence only; no model load/weight read/registration',inference_requested=False)))
'''
cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','hpc','/home/u202520081000097/jupyterlab/Paper/gosc/.venv/bin/python -']
p=subprocess.run(cmd,input=REMOTE.encode(),capture_output=True,timeout=30)
(LOG/'model_storage_stdout.json').write_bytes(p.stdout)
(LOG/'model_storage_stderr.txt').write_bytes(p.stderr)
print(json.dumps(dict(exit_code=p.returncode,response=json.loads(p.stdout) if p.returncode==0 else None)))
