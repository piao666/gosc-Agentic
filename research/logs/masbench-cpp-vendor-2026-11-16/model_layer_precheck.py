"""Read model manifest layer types only; no model load or HTTP."""
from pathlib import Path
import hashlib,json
p=Path('/home/u202520081000097/jupyterlab/models/ollama-gosc/manifests/registry.ollama.ai/library/qwen2.5/7b')
raw=p.read_bytes();m=json.loads(raw)
print(json.dumps({'manifest_sha256':hashlib.sha256(raw).hexdigest(),
    'layer_types':[x['mediaType'] for x in m['layers']],
    'unreviewed_default_layers':[x for x in m['layers'] if x['mediaType'].endswith(('.params','.messages','.system'))],
    'no_model_load':True,'http_requests':0}))
