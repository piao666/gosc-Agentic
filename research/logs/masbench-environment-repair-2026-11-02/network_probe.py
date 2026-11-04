"""One bounded public registry range probe on HPC; no model execution or file mutation."""
import json
import os
from pathlib import Path
import time
import urllib.parse
import urllib.request

url='https://registry.ollama.ai/v2/library/qwen2.5/blobs/sha256:5ee4f07cdb9beadbbb293e85803c569b01bd37ed059d2715faa7bb405f31caa6'
request=urllib.request.Request(url,headers={'Range':'bytes=964951504-965017039'})
started=time.monotonic()
try:
    with urllib.request.urlopen(request,timeout=12) as response:
        count=len(response.read(65536))
        result={'status':response.status,'read_bytes':count,'seconds':time.monotonic()-started,
                'content_range':response.headers.get('Content-Range'),
                'redirect_hostname':urllib.parse.urlsplit(response.url).hostname}
except Exception as error:
    result={'error_type':type(error).__name__,'seconds':time.monotonic()-started}
result['inference_requested']=False
(Path(os.environ['GOSC_OUTPUT_DIR'])/'range_probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
