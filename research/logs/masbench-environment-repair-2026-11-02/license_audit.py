"""Archive each public license layer separately; preserve the earlier run's ambiguous filenames."""
import hashlib
import json
import os
from pathlib import Path

root=Path('/home/u202520081000097/jupyterlab/Paper/gosc')
assert os.getuid()==8301880
source=root/'research/sync/runs/hpc-masbench-model-restore-after-storage-retry1-20261102/outputs/models_ready.json'
ready=json.loads(source.read_text());out=Path(os.environ['GOSC_OUTPUT_DIR'])
store=root.parents[1]/'models/ollama-gosc'
rows=[]
for name,info in ready['models'].items():
    raw=Path(info['manifest_path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==info['manifest_sha256']
    for layer in json.loads(raw)['layers']:
        if 'license' not in layer['mediaType']:continue
        digest=layer['digest'].split(':',1)[1]
        content=(store/'blobs'/('sha256-'+digest)).read_bytes()
        assert hashlib.sha256(content).hexdigest()==digest
        filename=name.replace(':','_')+'.'+digest[:12]+'.license.txt'
        target=out/filename
        assert not target.exists()
        target.write_bytes(content)
        rows.append({'model':name,'path':filename,'sha256':digest,'bytes':len(content)})
assert len({row['path'] for row in rows})==len(rows)
value={'source_run':'hpc-masbench-model-restore-after-storage-retry1-20261102',
       'license_layers':rows,'note':'Original models_ready.licenses used one filename per model; Llama has multiple license layers. Preserve that original output and use this unique-layer index instead.',
       'license_applicability_review':'Pending; layer archival is not legal approval','inference_requested':False}
(out/'license_layer_index.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'unique_license_layers':len(rows),'layer_hashes':'verified','inference_requested':False}))
