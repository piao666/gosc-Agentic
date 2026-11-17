"""Read fixed-source default-system preprocessing and its 68-byte model layer."""
from pathlib import Path
import hashlib,json
root=Path('/tmp/gosc-hpc-masbench-context-build-v3-20261116/source')
p=root/'server/routes.go';lines=p.read_text().splitlines();spans=[]
for i,line in enumerate(lines):
    if 'System' in line and ('m.System' in line or 'model.System' in line):
        spans.append({'line':i+1,'text':'\n'.join(lines[max(0,i-5):i+6])})
system=Path('/home/u202520081000097/jupyterlab/models/ollama-gosc/blobs/sha256-66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e').read_bytes()
print(json.dumps({'source_path':'server/routes.go','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'source_spans':spans,'default_system_size':len(system),'default_system_sha256':hashlib.sha256(system).hexdigest(),
    'default_system_text':system.decode(),'no_model_load':True},ensure_ascii=False))
